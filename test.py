def main():
    queue = []
    queue.append(("A","B"))
    queue.append(("C","D"))
    queue.append(("E","F"))

    while len(queue) > 0:
        print(queue.pop(0))


if __name__ == "__main__":
    main()