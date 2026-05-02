from time import sleep

def process_file(_: str, file_name: str):
    sleep(60)

    return {
        "filename": file_name,
        "status": "File processed"
    }
