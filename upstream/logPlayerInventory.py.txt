import minescript as mcs #type: ignore
from minescript_plus import Util #type: ignore

# Notes: Enchanted items have an nbt of None and the nbt data is trimmed anyway.
#           Solution? Java classes aka make your own mod

def textPrint(text):
    try:
        text = str(text)
        with open(r"C:\Github\Scripts-For-MCSMP\log.log", "a") as f:
            f.write(f"{text}\n\n\n")
    except:
        with open(r"C:\Github\Scripts-For-MCSMP\log.log", "a") as f:
            f.write("Error when appending\n\n\n")

def logPlayerInvetory():
    try:
        inv = mcs.player_inventory()
        for item in inv:
            textPrint(str(item))
    except:
        textPrint("Error in printing inventory information")
        
def main():
    open(r"C:\Github\Scripts-For-MCSMP\log.log", "w").close()
    logPlayerInvetory()

if __name__ == "__main__":
    main()