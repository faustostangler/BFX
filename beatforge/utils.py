# beatforge/utils.py

import time

def print_progress(index=0, size=1, start_time=None, extra_info=None, indent_level=0, indent_unit="  ", worker_id=None):
    """
    Exibe progresso, tempo decorrido, restante e total estimado.
    Pode ser chamado em qualquer loop com início conhecido.

    Args:
        index (int): índice atual (0-based).
        size (int): tamanho total.
        start_time (float): timestamp do início (time.time()).
        extra_info (list): lista de strings adicionais a exibir.
        indent_level (int): profundidade de indentação.
        indent_unit (str): caractere(s) para indentação (padrão: 2 espaços).
        worker_id (str): ID do worker (opcional).
    """
    if start_time is None:
        start_time = time.time()
    if extra_info is None:
        extra_info = []

    try:
        completed = index + 1
        remaining = size - completed
        pct = completed / size

        elapsed = time.time() - start_time
        avg = elapsed / completed
        remain = remaining * avg
        total = elapsed + remain

        # Format times
        def fmt(seconds):
            h, r = divmod(int(seconds), 3600)
            m, s = divmod(r, 60)
            return f"{h}h{m:02}m{s:02}s"

        worker_str = f"W{worker_id} " if worker_id else ""
        progress = (
            f"{pct:.2%} ({worker_str}{completed}/{size}), {avg:.4f}s/item, "
            f"{fmt(elapsed)}+{fmt(remain)}={fmt(total)}"
        )
        indent = indent_unit * (indent_level + 1)
        extra = " ".join(map(str, extra_info))
        print(f"{indent}{progress} {extra}")
    except Exception as e:
        print(f"Erro ao exibir progresso: {e}")
