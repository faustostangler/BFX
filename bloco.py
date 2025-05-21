import pandas as pd
from typing import Set, Tuple
from datetime import datetime

class BaseProcessor:
    """Interface genérica para processadores de dados."""
    def process(self) -> None:
        """Executa o processamento principal."""
        raise NotImplementedError("Process method must be implemented by subclasses")

class ScheduleTabulator(BaseProcessor):
    """
    Processador para tabular e apresentar informações de escalas de cirurgias
    agrupadas por weekday, turno e sala. Ao invés de imprimir,
    salva tudo em um arquivo texto.
    """
    def __init__(self, df: pd.DataFrame, output_path: str = 'agenda.txt'):
        """
        Inicializa com o DataFrame contendo as colunas:
        ['weekday', 'turno', 'room', 'date', 'time', 'procedures', 'surgeon']
        e define o arquivo de saída.
        """
        super().__init__()
        self.df = df.copy()
        self.output_path = output_path
        self._validate_columns()

    def _validate_columns(self) -> None:
        """Valida a presença de todas as colunas necessárias."""
        required: Set[str] = {
            'weekday', 'turno', 'room', 'date', 'time', 'procedures', 'surgeon'
        }
        missing = required - set(self.df.columns)
        if missing:
            raise ValueError(f"Faltando colunas obrigatórias: {missing}")

    def process(self) -> None:
        """Ponto de entrada do processamento."""
        self.tabulate()

    def tabulate(self) -> None:
        """
        Gera todo o texto em self.output_path, criando um nível extra:
        
        Na <weekday> na sala <room>:
          De <turno>:
            dia <DD/MM/YYYY>: ...
              - <n> cirurgias – <procedure> – <surgeon>
        
        A ordem de iteração é:
          1) weekday (prefixo numérico)
          2) room (numérico)
          3) turno (prefixo numérico)
        """
        with open(self.output_path, 'w', encoding='utf-8') as fh:
            # 1) combinações únicas weekday + room
            day_rooms = sorted(
                set(zip(self.df['weekday'], self.df['room'])),
                key=lambda x: (
                    int(x[0].split(' - ')[0]),       # prefixo de weekday
                    int(x[1]) if str(x[1]).isdigit() else x[1]
                )
            )
            prev_weekday = None
            for weekday, room in day_rooms:
                # se mudou o weekday, escreve separador
                if weekday != prev_weekday:
                    if prev_weekday is not None:
                        fh.write("--------------------\n\n")
                    prev_weekday = weekday

                # cabeçalho de weekday + sala
                fh.write(f"*Na ({weekday}) na (sala {room}):*\n")

                # filtra só este weekday+sala
                df_dr = self.df[
                    (self.df['weekday'] == weekday) &
                    (self.df['room']    == room)
                ]

                # 2) itera turnos dentro deste bloco, ordenados pelo prefixo numérico
                turnos = sorted(
                    df_dr['turno'].unique(),
                    key=lambda t: int(t.split(' - ')[0])
                )
                for turno in turnos:
                    # exibe só o nome do turno (sem o número e " - ")
                    turno_label = turno.split(' - ', 1)[1]
                    fh.write(f"  *De {turno_label}*:\n")

                    # filtra também pelo turno
                    df_tr = df_dr[df_dr['turno'] == turno]

                    # 3) itera cada data neste sub-bloco
                    for date, sub in df_tr.groupby('date'):
                        date_str = date.strftime('%d/%m/%Y')
                        times = sorted(sub['time'].astype(str))
                        if len(times) == 1:
                            fh.write(f"    - dia {date_str}: somente uma cirurgia às {times[0]}\n")
                        else:
                            fh.write(
                                f"    - dia {date_str}: \n"
                                f"      primeira às {times[0]}, última marcada às {times[-1]}\n"
                            )

                        # elimina linhas sem centro, surgeon ou procedure
                        valid = sub.dropna(subset=['centro', 'surgeon', 'procedures'])

                        # conta quantas vezes cada combinação centro+surgeon+procedure aparece
                        pair_counts = (
                            valid
                            .groupby(['centro', 'surgeon', 'procedures'])
                            .size()
                            .reset_index(name='count')
                        )

                        # escreve cada combinação já com o centro no meio
                        for _, row in pair_counts.sort_values(
                                ['count','centro','procedures','surgeon']
                            ).iterrows():

                            cnt       = row['count']
                            centro    = row['centro']
                            procedure = row['procedures']
                            surgeon   = row['surgeon']
                            label     = 'cirurgia' if cnt == 1 else 'cirurgias'

                            fh.write(
                                f"      - {cnt} {label} – ({centro}) – {procedure} – {surgeon}\n"
                            )

                fh.write("\n")  # separa blocos de salas
            fh.write("\n\n")  # separa blocos de salas
        print(f"Agenda salva em: {self.output_path}")


if __name__ == "__main__":
    # --- Leitura do CSV e preparação do DataFrame ---
    df = pd.read_csv(
        'escala_bloco.csv',
        parse_dates=['date'],
        dayfirst=True  # formato DD/MM/YYYY
    )
    # garante que 'time' esteja no formato HH:MM
    df['time'] = pd.to_datetime(df['time'], format='%H:%M').dt.strftime('%H:%M')
    # deriva weekday em português, caso ainda não exista
    # df['weekday'] = df['date'].dt.day_name(locale='pt_BR')

    # --- Instancia e salva ---
    tabulator = ScheduleTabulator(df, output_path='escala semanal.txt')
    tabulator.process()

print('done!')