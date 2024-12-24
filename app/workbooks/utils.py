def getMergedCellVal(sheet, cell):
    rng = [s for s in sheet.merged_cells.ranges if cell.coordinate in s]
    return (
        sheet.cell(rng[0].min_row, rng[0].min_col).value
        if len(rng) != 0
        else cell.value
    )
