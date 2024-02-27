#!/usr/bin/env python3
# Created by B Haddow and modified by P Chen to generate LaTeX tables from eval.tsv

import pandas
import sys


def main():
    all_results = pandas.read_csv("eval.tsv", sep="\t")

    for filename, metric in (
        ("tbl-eval-bleu.tex", "BLEU"),
        ("tbl-eval-chrf.tex", "ChrF"),
        ("tbl-eval-comet.tex", "COMET"),
    ):
        pairs = all_results["pair"].unique()
        with open(filename, "w") as out:
            print("% Generated by make_eval_tables.py DO NOT EDIT", file=out)
            print("\\begin{tabular}{|c|ccc|ccc|}", file=out)
            print("\\hline", file=out)
            print(
                " & \\multicolumn{3}{c|}{\\textbf{FLORES-200}} & \multicolumn{3}{c|}{\\textbf{NTREX}} \\\\",
                file=out,
            )
            print("\\cline{2-7}", file=out)
            print(
                " Pair & \phantom{0}HPLT\phantom{0} & \phantom{0}OPUS\phantom{0} & HPLT+OPUS & \phantom{0}HPLT\phantom{0} & \phantom{0}OPUS\phantom{0} & HPLT+OPUS \\\\",
                file=out,
            )
            print("\\hline", file=out)

            for pair in pairs:
                pair_str = pair.replace("_", "\\_")
                print(pair_str, file=out, end="")
                for testset in "flores", "ntrex":
                    max_result = all_results[
                        (all_results.pair == pair) & (all_results.test == testset)
                    ][metric].max()
                    for trainset in "hplt", "opus", "opus_hplt":
                        results = all_results[
                            (all_results.train == trainset)
                            & (all_results.pair == pair)
                            & (all_results.test == testset)
                        ]
                        assert len(results == 1), (
                            "Problem at: " + pair + " " + testset + " " + trainset
                        )
                        result_number = results[metric].values[0]
                        if metric == "COMET":
                            number_str = "{0:.4f}".format(result_number)
                        else:
                            number_str = "{0:.1f}".format(result_number)
                            if result_number < 10:
                                number_str = " \\phantom{0}" + number_str
                        if result_number == max_result:
                            number_str = "\\textbf{" + number_str + "}"
                        print(" & " + number_str, file=out, end="")
                print("\\\\", file=out)

            print("\\hline", file=out)
            print("\\end{tabular}", file=out)


if __name__ == "__main__":
    main()