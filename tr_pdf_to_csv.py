import os
from utils import *

path_ = "./pdf_files/"

lst_pdfs, lst_paths = get_pdf_files(path_)

for i, path_ in enumerate(lst_paths):

    try:
        doc_in_lines = pdf_to_txt(path_)
    except Exception as e:
        print(f"Error converting {lst_paths[i]} to text: {e}")
        continue  # Skip to the next file

    try:
        dct_info = extract_doc_info(doc_in_lines)
    except Exception as e:
        print(f"Error extracting info from {lst_paths[i]}: {e}")
        continue  # Skip to the next file

    try:
        df = txt_to_df(doc_in_lines, dct_info)
    except Exception as e:
        print(f"Error converting text to DataFrame for {lst_paths[i]}: {e}")
        continue  # Skip to the next file

    try:
        export_file = path_.replace('pdf', 'csv')
        df.to_csv(export_file, index=False)
    except Exception as e:
        print(f"Error saving CSV for {lst_paths[i]}: {e}")
        continue  # Skip to the next file

    print(f'{lst_paths[i]} successfully converted!')





