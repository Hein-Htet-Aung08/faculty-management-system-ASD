def row_to_dict(row):
    return dict(row) if row else None
 
 
def rows_to_list(rows):
    return [dict(r) for r in rows]