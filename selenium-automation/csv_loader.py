import csv
import queue
import sys
from text_ui import TextUI


def load_csv_to_queue(file_path):
    data_queue = queue.Queue()

    try:
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            # Read the first line for issuerId
            issuer_id_line = next(csvfile).strip().split(',')
            if issuer_id_line[0].lower() != 'issuerid':
                raise ValueError("First line must contain issuerId.")
            issuer_id = issuer_id_line[1]

            # Skip the header line
            next(csvfile)

            # Process the rest of the file for user data
            csv_reader = csv.DictReader(csvfile, fieldnames=['email', 'userId'])
            for row in csv_reader:
                data_queue.put({
                    'issuerId': issuer_id,
                    'userId': row['userId'],
                    'email': row['email']
                })
            TextUI.success("CSV successfully loaded.")

    except FileNotFoundError:
        TextUI.error("File not found. Please check the file path.")
        sys.exit(1)
    except ValueError as e:
        TextUI.error(f"Error: {e}")
        sys.exit(1)

    return data_queue
