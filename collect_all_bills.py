import sys
from pathlib import Path
import pandas as pd

def main():
    folder = sys.argv[1]
    paths = Path(folder).glob("*.csv")
    writer = pd.ExcelWriter(folder+".xlsx")
    for path in paths:
        df = pd.read_csv(
            path, sep=";", encoding="cp1252", decimal=b",", parse_dates=[4, 5]
        )
        df.to_excel(writer, sheet_name=path.stem)
    writer.save()

if __name__ == "__main__":
    main()