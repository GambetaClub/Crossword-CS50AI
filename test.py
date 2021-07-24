def main():
    dic = {"key1": "value1", "key2": "value2", "key3": "", "key4": "value4"}

    for variable in dic:
        if dic[variable]:
            print(f"Variable: {variable} has the value {dic[variable]}")
        else:
            print(f"Variable: {variable} doesn't have any value")


if __name__ == "__main__":
    main()