from portfolio_qaoa import build_instance, build_qubo, solve_with_qaoa

def main():
    tickers, mu, Sigma, budget, lam = build_instance()
    qp = build_qubo(tickers, mu, Sigma, budget, lam)

    result = solve_with_qaoa(qp, reps=2)

    print("Resultado QAOA:")
    print(result)
    print("Selecionados:", [k for k,v in result.variables_dict.items() if v > 0.5])

if __name__ == "__main__":
    main()
