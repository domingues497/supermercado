def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF com base nos dígitos verificadores.
    Remove caracteres não numéricos e aplica o algoritmo.
    """
    cpf = ''.join(filter(str.isdigit, cpf))

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    def calc_digito(digs):
        s = sum(int(d) * f for d, f in zip(digs, range(len(digs)+1, 1, -1)))
        d = (s * 10) % 11
        return str(d if d < 10 else 0)

    primeiro = calc_digito(cpf[:9])
    segundo = calc_digito(cpf[:9] + primeiro)

    return cpf[-2:] == primeiro + segundo
