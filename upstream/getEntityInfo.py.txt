import minescript as mcs #type: ignore

def textPrint(text):
    try:
        text = str(text)
        with open(r"C:\Github\Scripts-For-MCSMP\log.log", "a") as f: #appending to a textfile
            f.write(f"{text}\n\n\n")
    except:
        with open(r"C:\Github\Scripts-For-MCSMP\log.log", "a") as f: #appending to a textfile
            f.write("Error when appending\n\n\n")

def viewEntityInformation(entity):
    try:
        info = (
            f"name={entity.name}, \n"
            f"type={entity.type}, \n"
            f"pos={entity.position}, \n"
            f"health={entity.health}"
        )

        nbt = str(entity.nbt)
        prettynbt = nbt.replace(",", ",\n").replace("{", "{\n").replace("}", "\n}")

        textPrint(f"{info}\n{prettynbt}")
    except:
        textPrint("Error in printing entity information")

def main():
    target = mcs.player_get_targeted_entity(nbt=True)
    viewEntityInformation(target)

if __name__ == "__main__":
    open(r"C:\Github\Scripts-For-MCSMP\log.log", "w").close()
    main()