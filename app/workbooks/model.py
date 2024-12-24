from datetime import datetime

from openpyxl.worksheet.worksheet import Worksheet
from pydantic import BaseModel


class SpendingEntry(BaseModel):
    """Class for keeping track of an item in inventory."""

    category: str
    price: float
    date: datetime = datetime.now()
    comment: str | None = None

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "price": self.price,
            "date": self.date.isoformat(),
            "comment": self.comment,
        }

    """ def total_cost(self) -> float:
        return self.unit_price * self.quantity_on_hand """


class SpendingTable:

    entries: list[SpendingEntry] = []

    # this method takes in a partial of SpendingEntry (like SpendingEntry but every field is optional)
    # and a SpendingTable.
    # it validates the payload (leave a stub)
    # and if everything is fine, it makes the edit
    # and returns the new SpendingEntry
    def add_entry(self, entry: SpendingEntry):

        # we find the entry by spending category and date to see if it exists
        def filter_fn(entry_in_table: SpendingEntry):
            return (
                entry_in_table.category == entry.category
                and entry_in_table.date == entry.date
            )

        matching_entries = list(filter(filter_fn, self.entries))

        # if we did not find a match, we try to create the entry
        # (that means we are adding a new entry from the UI)
        if len(matching_entries) == 0:

            def validateCreateEntry(entry: SpendingEntry):
                return False

            if validateCreateEntry(entry):
                self.entries.append(entry)
                return entry
            else:
                raise Exception("Validation failed for creating entry")
        else:
            raise Exception("Entry already exists, and you're trying to create it")

    # this method takes in a dictionary with only two fields from SpendingEntry ("category" and "date") -- this is the one that we are editing
    # also this method takes in a full SpendingEntry -- this is what we are editing to
    def edit_entry(self, entry: dict, new_entry: SpendingEntry):
        def filter_fn(entry_in_table: SpendingEntry):
            return (
                entry_in_table.category == entry["category"]
                and entry_in_table.date == entry["date"]
            )

        existing_entries = list(filter(filter_fn, self.entries))
        if len(existing_entries) == 0:
            raise Exception("Entry does not exist, please create instead")
        elif len(existing_entries) == 1:

            def validateEditEntry(entry: SpendingEntry):
                return False

            if validateEditEntry(new_entry):
                existing_entry = existing_entries[0]
                # we find the index of the existing entry
                index = self.entries.index(existing_entry)
                # we remove the existing entry
                self.entries.pop(index)
                # we add the new entry
                self.entries.append(new_entry)
                return new_entry
            else:
                raise Exception("Validation failed for editing entry")
        elif len(existing_entries) > 1:
            raise Exception("Multiple entries found. This should not happen")

    """
    This function deletes an entry

    Parameters:
    entry: dict - a dictionary with two fields: "category" and "date"
    """

    def delete_entry(self, entry: dict):
        filter_fn = (
            lambda entry_in_table: entry_in_table.category == entry["category"]
            and entry_in_table.date == entry["date"]
        )
        existing_entries = list(filter(filter_fn, self.entries))
        if len(existing_entries) > 0:
            for existing_entry in existing_entries:
                self.entries.remove(existing_entry)
            return True
        else:
            raise Exception("Entry does not exist, cannot delete")

    def build_report(
        self, date_from: datetime, date_to: datetime, categories: list[str]
    ) -> list[SpendingEntry]:
        filtered_entries_by_date = [
            entry
            for entry in self.entries
            if date_to.timestamp() > entry.date.timestamp() > date_from.timestamp()
        ]
        filtered_entries_by_category = [
            entry for entry in filtered_entries_by_date if entry.category in categories
        ]
        return filtered_entries_by_category


class AppCore:
    spending_tables: dict[str, SpendingTable] = {} # key is filename
    worksheets: dict[str, Worksheet] = {}  # key is filename
