import sys
import pandas as pd
from datetime import timedelta
from pathlib import Path


class Bill:

    header = [
        "avtalenr", "fakturanr", "brikkenr", "regnr", "passeringstid",
        "belastningstid", "belop", "mva", "bomstasjon",
        "bomstasjonfil", "bomstasjonsoperator"
    ]
    inspect_cols = [
        "passeringstid", "belastningstid", "belop", "bomstasjon",
        "timediff", "is_hour", "is_charged", "is_correct",
        "is_free", "is_catastrofy"
    ]

    def __init__(self, path):
        self.df = pd.read_csv(
            path, sep=";", encoding="cp1252", header=0,
            decimal=b",", parse_dates=[4, 5], names=self.header
        )
        self.path = path
        self.sort_by_passering()
        self.add_timediff()
        self.add_is_hour()
        self.add_is_charged()
        self.add_is_correct()
        self.add_is_free()
        self.add_is_catastrofy()
        self.should_inspect_first = self.df.loc[0, "passeringstid"].hour < 1

    def sort_by_passering(self):
        '''Sort df by passeringstid, ascending.'''
        self.df.sort_values("passeringstid", inplace=True)
        self.df.reset_index(inplace=True)

    def add_timediff(self):
        '''
        Add timediff to df for each passeringstid.
        No timediff for the first observartion.
        '''
        self.df["timediff"] = self.df["passeringstid"].diff()

    def add_is_hour(self):
        '''Add boolean to df for each timediff > 60 min.'''
        self.df["is_hour"] = (self.df["timediff"] > timedelta(hours=1))

    def add_is_charged(self):
        '''Add boolean to df for every belop > 0.'''
        self.df["is_charged"] = self.df["belop"] > 0

    def add_is_correct(self):
        '''
        Add boolean to df for every correct payment.
        First observation is assumed to be correct.
        '''
        self.df["is_correct"] = (self.df["is_hour"] == self.df["is_charged"])
        self.df.loc[0, "is_correct"] = True

    def add_is_free(self):
        '''Add boolean to df for every free passing.'''
        self.df["is_free"] = (
            (self.df["is_hour"] == True) & (self.df["is_charged"] == False)
        )

    def add_is_catastrofy(self):
        '''
        Add boolean to df for every incorrect payment.
        First payment is assumed to be correct.
        '''
        self.df["is_catastrofy"] = (
            (self.df["is_hour"] == False) & (self.df["is_charged"] == True)
        )
        self.df.loc[0, "is_catastrofy"] = False

    def status(self):
        '''Print human readable status.'''
        fakturanr = self.df["fakturanr"].unique().tolist()
        regnr = self.df["regnr"].unique().tolist()
        brikkenr = self.df["brikkenr"].unique().tolist()
        sub_total = self.df["belop"].sum()
        free_passings = self.df.loc[
            self.df["is_free"], "passeringstid"
        ]
        catastrofies = self.df.loc[
            self.df["is_catastrofy"], ["passeringstid", "bomstasjon", "belop"]
        ]

        print()
        print("File: ", self.path)
        print("{:<20}: {:>20}".format(
            "Inspiser forste", "Ja" if self.should_inspect_first else "Nei"
            )
        )
        print("{:<20}: {:>20}".format("Brikkenr ", *brikkenr))
        print("{:<20}: {:>20}".format("Faktura", *fakturanr))
        print("{:<20}: {:>20}".format("Regnr ", *regnr))
        print("{:<20}: {:>20}".format("Sum ", round(sub_total, 1)))
        print("Gratis passeringer:")
        print(
            free_passings.to_string() if not free_passings.empty
            else "Ingen...=/"
        )
        print("Inspiser passeringer:")
        print(
            catastrofies.to_string() if not catastrofies.empty else "Ingen!:D"
        )
        print()

    def inspect(self):
        print(self.df[self.inspect_cols])


def main():
    folder = sys.argv[1]
    writer = pd.ExcelWriter(folder+".xlsx")
    paths = Path(folder).glob("*.csv")
    for path in paths:
        bill = Bill(path)
        bill.status()
        bill.df.to_excel(writer, sheet_name=path.stem)
    writer.save()


if __name__ == "__main__":
    main()
