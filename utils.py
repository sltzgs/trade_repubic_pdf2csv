import os
import pymupdf
import numpy as np
import pandas as pd

def get_pdf_files(folder_path='./'):
    # List all files in the specified folder and filter for .pdf files
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]
    pdf_file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.pdf')]
    return pdf_files, pdf_file_paths

def pdf_to_txt(path):
    # Open the document and extract text from all pages
    with pymupdf.open(path) as doc:
        doc_text = "\n".join(page.get_text() for page in doc)

    # Return the extracted text as a list of lines
    return doc_text.splitlines()

#------------------------------ helpers for doc info extraction ------------------------------#
def find_iban(doc_in_lines):
    i_line = np.where([line_i == 'IBAN' for line_i in doc_in_lines])[0][0]
    return doc_in_lines[i_line+1]

def find_user_info(doc_in_lines):
    list_upper = []
    for line_ in doc_in_lines:
        if line_.isupper():
            list_upper.append(line_)

    for uq_upper in np.unique(list_upper):
        if (len(uq_upper.split(' ')) > 1) & (uq_upper != doc_in_lines[26]):
            user_name = uq_upper

    i_line = np.where([line_i==user_name for line_i in doc_in_lines])[0][0]
    user_address = doc_in_lines[i_line:i_line+2]
    return user_name, user_address

def find_last_line(doc_in_lines):
    # based on last "€"
    last_line = int(np.where(["€" in line_ for line_ in doc_in_lines])[0][-1]) + 1
    return last_line

def extract_doc_info(doc_in_lines):

    user_name, user_address = find_user_info(doc_in_lines)
    iban = find_iban(doc_in_lines)
    saldo_init = str_to_float(doc_in_lines[18][:-2])
    last_line = find_last_line(doc_in_lines)
    date_init = doc_in_lines[6].split('-')[0]

    df = pd.DataFrame(columns=[i for i in doc_in_lines[23:28]])
    df.loc[0] = [date_init, 'INITIAL SALDO', '-', '-', saldo_init]

    dct_info = {'df': df,
                'user_name': user_name,
                'user address': user_address,
                'IBAN': iban,
                'date_init': date_init,
                'saldo_init': saldo_init,
                'last_line': last_line}

    return dct_info

#------------------------------ helpers for text to pd.DataFrame conversion ------------------------------#

def is_new_page(line):
    if line=='':
        return True
    else:
        return False

def str_to_float(string):
    # required due to currency format
    float_ = float(string.replace(".", "").replace(",", "."))
    return float_

def init_counters():
    line_, page_current, i_entry, line_add = 28,0,1,0
    return page_current, i_entry, line_add, line_

def is_user_info(line, user_name):
    if line==user_name:
        return True
    else:
        return False

def skip_lines(doc_in_lines, i_line, dct_info):
    #Skips lines based on the current line's content and specified conditions.

    if is_new_page(doc_in_lines[i_line]): # approx. 10 lines - next condition takes care of exact amount to skip
        return i_line + 10, True
    if doc_in_lines[i_line] in dct_info['df'].columns:
        return i_line + 1, True

    if is_user_info(doc_in_lines[i_line], dct_info['user_name']):
        return i_line + 3, True

    return i_line, False

def txt_to_df(doc_in_lines, dct_info):

    saldo_old = dct_info['saldo_init']
    df = dct_info['df']

    i_page, i_entry, line_add, i_line = init_counters()
    lst_years = [str(year) for year in range(1900, 2100)]

    while i_line < dct_info['last_line']:

        # Detect new page and skip initial entries
        is_skip=True
        while is_skip:
            i_line, is_skip = skip_lines(doc_in_lines, i_line, dct_info)

        # get date of current transaction
        i_year = np.where([line_ in lst_years for line_ in doc_in_lines[i_line:i_line+10]])[0][0]
        date_ = "".join(doc_in_lines[i_line:i_line+i_year+1])
        i_line += i_year+1

        # get type of current transaction
        type_ = doc_in_lines[i_line].split(" ")[0]

        # get details of current entry
        i_eur = np.where([['€' in i] for i in doc_in_lines[i_line:i_line + 100]])[0][0]  # find next entry with currency
        details_ = " ".join(doc_in_lines[i_line].split(" ")[1:]+[i for i in doc_in_lines[i_line+1:i_line+i_eur]])
        i_line += i_eur

        # get amount, sign and new saldo of current transaction
        saldo_new = str_to_float(doc_in_lines[i_line+1][:-2])
        amount_ = np.round(saldo_new - saldo_old,2)
        if abs(amount_) != str_to_float(doc_in_lines[i_line][:-2]):
            print(f'WARNING - SALDO ERROR FOR ENTRY {i_entry}')
            print(abs(amount_), str_to_float(doc_in_lines[i_line][:-2]))

        # write transaction to DataFrame
        df.loc[i_entry] = [date_, type_, details_, amount_, saldo_new]

        saldo_old = np.copy(saldo_new)

        # Handle counters
        i_line += 2
        i_entry +=1

    return df