def main():
    make_dict()

    # Return dictionary of values from a db column
def make_dict(db_column):
    key = 0
    dict = { }
    for value in db_column:
        dict[str(key)] = value
        key = key + 1
    return dict

if __name__ == "__main__":
    main()