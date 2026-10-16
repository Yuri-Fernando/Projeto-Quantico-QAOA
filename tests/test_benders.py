import numpy as np
import pytest

from optimization.benders import solve_benders
from optimization.instance import build_instance
from optimization.stochastic import solve_stochastic_extensive_form


@pytest.fixture
def instance():
    return build_instance()


def test_benders_converges(instance):
    result = solve_benders(instance, max_iter=30, tol=1e-6)
    assert result["converged"]
    assert result["iterations"] <= 30


def test_benders_matches_monolithic_relaxed_stochastic(instance):
    """O master do Benders é a relaxação contínua de x — então o resultado
    da decomposição deve coincidir com resolver a forma extensiva do
    estocástico com x relaxado, resolvida de uma vez só (sem decomposição).
    Esse é o teste de corretude central do Benders: o loop de cortes real
    deve convergir para o mesmo ótimo que o solver monolítico encontra
    diretamente."""
    benders_result = solve_benders(instance)
    monolithic = solve_stochastic_extensive_form(instance, integer_first_stage=False)

    assert np.isclose(benders_result["objective"], monolithic["objective"], atol=1e-4)
