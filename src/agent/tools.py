def read_file_to_word_list():
    file_location = input("Please enter the file location: ")
    try:
        with open(file_location, "r") as file:
            contents = file.read()
            words = contents.split(",")
            words = [word.strip() for word in words]
            return words
    except FileNotFoundError:
        print(f"File not found: {file_location}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
