"""Executable doctest examples for the Veyra Sage laboratory.

Modes preserve Veyra resonance methods:

>>> from veyra_sage.all import VeyraModes
>>> M = VeyraModes("abc")
>>> M("ab").cyclic_resonates(M("baba"))
True

Balances expose signed shadows explicitly:

>>> from veyra_sage.all import VeyraBalances
>>> B = VeyraBalances("τ")
>>> (B(3) + B(-2)).net_length()
1

Ratios keep Veyra objects and declare shadows:

>>> from veyra_sage.all import VeyraRatios
>>> Q = VeyraRatios("τ")
>>> print((Q(1, 2) + Q(1, 3)).shadow())
5/6

Polynomials stay over Veyra ratios:

>>> from veyra_sage.all import VeyraPolynomials
>>> P = VeyraPolynomials("τ", "x")
>>> product = P([1, 1]) * P([-1, 1])
>>> [str(item) for item in product.coefficient_shadows()]
['-1', '0', '1']
>>> print(product.evaluate(3).shadow())
8
>>> [str(item) for item in product.derivative().coefficient_shadows()]
['0', '2']

School-core facade exposes theorem/curriculum registry summaries:

>>> from veyra_sage.all import VeyraSchoolCore
>>> S = VeyraSchoolCore()
>>> S.summary()["theorem_specs"]
19
>>> S.curriculum_node("statistics").status
'covered'
>>> len(S.export_rows())
38

Proof graph exposes dependencies and curriculum paths:

>>> from veyra_sage.all import VeyraProofGraph
>>> G = VeyraProofGraph()
>>> "pythagorean-separation" in G.theorems_using("DEF-088")
True
>>> G.curriculum_path("arithmetic-ratios", "statistics")
('arithmetic-ratios', 'combinatorics', 'probability', 'statistics')

Notebook exporter produces markdown/ipynb-ready lab artifacts:

>>> from veyra_sage.all import build_school_proof_notebook
>>> N = build_school_proof_notebook()
>>> N.summary()["cells"]
8
>>> N.to_ipynb_dict()["nbformat"]
4

Domain notebooks split the proof graph into focused labs:

>>> from veyra_sage.all import available_notebook_domains, build_domain_theorem_notebook
>>> "geometry" in available_notebook_domains()
True
>>> build_domain_theorem_notebook("geometry").summary()["cells"]
8

Executable card examples run proof checks:

>>> from veyra_sage.all import card_example_summary, run_card_example
>>> card_example_summary()["ready"]
19
>>> run_card_example("pythagorean-separation").status
'ready'

Refutation examples must block intentionally bad cards:

>>> from veyra_sage.all import refutation_summary, run_refutation_example
>>> refutation_summary()["blocked"]
7
>>> run_refutation_example("pythagorean-non-right").status
'blocked'

Parameterized refutation search finds blocked candidates:

>>> from veyra_sage.all import refutation_search_summary, run_search_candidate
>>> refutation_search_summary()["blocked"]
7
>>> run_search_candidate("geo-right").status
'ready'
>>> run_search_candidate("geo-non-right").status
'blocked'
"""
