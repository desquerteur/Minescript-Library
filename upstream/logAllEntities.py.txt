import minescript as mcs #type: ignore

def textPrint(text):
    try:
        text = str(text)
        with open(r"C:\Github\Scripts-For-MCSMP\log.log", "a") as f: #appending to a textfile
            f.write(f"{text}\n\n\n")
    except:
        with open(r"C:\Github\Scripts-For-MCSMP\log.log", "a") as f: #appending to a textfile
            f.write("Error when appending\n\n\n")

def logAllEntities():
    entities = mcs.entities()
    for e in entities:
        textPrint(str(e))

def logAllItemEntities():
    entities = mcs.entities(type="entity.minecraft.item")
    for e in entities:
            textPrint(str(e))

def main():
    open(r"C:\Github\Scripts-For-MCSMP\log.log", "w").close() #wipes previous log data
    logAllEntities()

if __name__ == "__main__":
    main()