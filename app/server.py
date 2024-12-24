from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from auth.core import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_active_user,
)
from auth.model import Token, User
from auth.users import USERS_DB
import workbooks.core as core
import workbooks.model as model
import documents.core as documents

from typing import Annotated

app = FastAPI()
origins = [
    "http://localhost:4321",
    "https://2ym2-7i13-9ujg.gw-1a.dockhost.net:8080",
]

prefix_router = APIRouter(prefix="/server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app_model = model.AppCore()


@prefix_router.post("/upload")
async def upload_excel(file: UploadFile = File(...)):

    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="Invalid file format. Please upload an Excel file."
        )

    try:
        sheet = await core.read_workbook_from_bytes(file)
        if sheet is None:
            raise HTTPException(403, "No worksheet in file")

        results = core.workbook_to_rows(sheet)
        app_model.spending_tables[file.filename] = (
            core.build_spending_table_from_results(results, sheet)
        )
        app_model.worksheets[file.filename] = sheet
        print(app_model.spending_tables[file.filename].entries)
        # Return the results as JSON
        return JSONResponse(
            content={
                "status": "success",
                "data": [
                    entry.to_dict()
                    for entry in app_model.spending_tables[file.filename].entries
                ],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@prefix_router.get("/document/list", tags=["document"])
async def list_documents(
    # current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        files = await documents.get_all_documents()
        response_data = {"files": files}

        # Return the results as JSON
        return JSONResponse(
            content={
                "status": "success",
                "data": response_data,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")


@prefix_router.get("/document", tags=["document"])
async def get_document(filename: str):
    if not filename or not filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please provide a valid filename.",
        )

    try:
        # sheet = await core.read_workbook_from_bytes(file)
        sheet = await core.read_workbook(f"documents_storage/{filename}")

        if sheet is None:
            raise HTTPException(403, "No worksheet in file")

        results = core.workbook_to_rows(sheet)

        app_model.spending_tables[filename] = core.build_spending_table_from_results(
            results, sheet
        )
        app_model.worksheets[filename] = sheet
        print(app_model.spending_tables[filename].entries)
        # Return the results as JSON
        return JSONResponse(
            content={
                "status": "success",
                "data": [
                    entry.to_dict()
                    for entry in app_model.spending_tables[filename].entries
                ],
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    try:
        file = await documents.get_document(filename)
        response_data = {"filename": filename}

        # Return the results as JSON
        return JSONResponse(
            content={
                "status": "success",
                "data": response_data,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file: {str(e)}")


@prefix_router.post("/document", tags=["document"])
async def upload_document(file: UploadFile = File(...)):

    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="Invalid file format. Please upload an Excel file."
        )

    try:
        """
        sheet = await core.read_workbook(file)
        if sheet is None:
            raise HTTPException(403, "No worksheet in file")

        results = core.workbook_to_rows(sheet)
        app_model.spending_table = core.build_spending_table_from_results(
            results, sheet
        )
        app_model.worksheet = sheet
        print(app_model.spending_table.entries)
        """

        await documents.save_document(file)
        response_data = {"filename": file.filename}

        # Return the results as JSON
        return JSONResponse(
            content={
                "status": "success",
                "data": response_data,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@prefix_router.post("/document/rename", tags=["document"])
async def rename_document(old_name: str, new_name: str):

    if (
        not old_name
        or not old_name.endswith((".xlsx", ".xls"))
        or not new_name
        or not new_name.endswith((".xlsx", ".xls"))
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid input. Make sure you provided two names and they're both XLS or XLSX",
        )

    try:
        await documents.rename_document(old_name, new_name)
        response_data = {"filename": new_name}

        # Return the results as JSON
        return JSONResponse(
            content={
                "status": "success",
                "data": response_data,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renaming file: {str(e)}")


@prefix_router.delete("/document", tags=["document"])
async def delete_document(filename: str):
    if not filename or not filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Please provide a valid filename.",
        )

    try:
        await documents.delete_document(filename)
        response_data = {"filename": filename}

        # Return the results as JSON
        return JSONResponse(
            content={
                "status": "success",
                "data": response_data,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


"""unused endpoint"""
"""
@prefix_router.post("/filter")
async def filter_report(date_from: datetime, date_to: datetime, categories: list[str]):

    if not app_model.spending_table:
        raise HTTPException(
            status_code=400, detail="No data to filter. Please upload a file first."
        )

    try:
        filtered_data = app_model.spending_table.build_report(
            date_from, date_to, categories
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering data: {str(e)}")

    return JSONResponse(content={"status": "success", "data": filtered_data})
"""


@prefix_router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(USERS_DB, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@prefix_router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@prefix_router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]


@prefix_router.put("/entries/{workbook_name}", tags=["entries"])
def edit_entry(
    workbook_name: str,
    old_entry_date: datetime,
    old_entry_category: str,
    entry: model.SpendingEntry,
):
    try:
        if workbook_name not in app_model.spending_tables:
            raise HTTPException(
                status_code=400,
                detail="Workbook has not been read. It is possible that the file does not exist.",
            )

        app_model.spending_tables[workbook_name].edit_entry(
            {"date": old_entry_date, "category": old_entry_category}, entry
        )

        return JSONResponse(content={"status": "success"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error editing entry: {str(e)}")


@prefix_router.post("/entries/{workbook_name}", tags=["entries"])
def create_entry(
    workbook_name: str,
    entry: model.SpendingEntry,
):
    try:
        if workbook_name not in app_model.spending_tables:
            raise HTTPException(
                status_code=400,
                detail="Workbook has not been read. It is possible that the file does not exist.",
            )

        app_model.spending_tables[workbook_name].add_entry(entry)

        return JSONResponse(content={"status": "success"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating entry: {str(e)}")


@prefix_router.delete("/entries/{workbook_name}", tags=["entries"])
def delete_entry(workbook_name: str, entry_date: datetime, entry_category: str):
    try:
        if workbook_name not in app_model.spending_tables:
            raise HTTPException(
                status_code=400,
                detail="Workbook has not been read. It is possible that the file does not exist.",
            )

        app_model.spending_tables[workbook_name].delete_entry(
            {"date": entry_date, "category": entry_category}
        )

        return JSONResponse(content={"status": "success"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting entry: {str(e)}")


app.include_router(prefix_router)

# Run the app with: uvicorn filename:app --reload
# Create the requirements.txt file with: pip freeze > requirements.txt
