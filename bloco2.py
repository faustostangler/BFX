import os
import re
import glob
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from collections import OrderedDict
from typing import Dict, List, Optional, Any

import pdfplumber
import pandas as pd
from datetime import datetime, time

# Configurações de logging para suprimir warnings desnecessários
logging.getLogger("pdfminer").setLevel(logging.ERROR)


class BaseProcessor(ABC):
    """
    Abstração de um processador no pipeline, definindo contrato de entrada e saída.
    """

    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """
        Executa o processamento e retorna o resultado.
        """
        pass


class PDFScheduleParser(BaseProcessor):
    """
    Processa todos os PDFs de um diretório, extraindo blocos de texto por data e centro.

    Retorna estrutura:
      { filename: { date: { centro: [linhas...] } } }
    """

    def __init__(self, pdf_dir: str):
        super().__init__()
        self.pdf_dir = pdf_dir
        self.paths = glob.glob(os.path.join(self.pdf_dir, '*.pdf'))

    def process(self) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
        content: Dict[str, Dict[str, Dict[str, List[str]]]] = {}
        for i, path in enumerate(self.paths, 1):
            filename = os.path.basename(path)
            content[filename] = self._parse_single(path)
            print(f'{i}/{len(self.paths)}. {filename}')
        return content

    def _parse_single(self, path: str) -> Dict[str, Dict[str, List[str]]]:
        pages_by_date: Dict[str, Dict[str, List[str]]] = {}
        current_block = None
        buffer: List[str] = []
        current_date: Optional[str] = None

        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ''
                lines = text.splitlines()
                if len(lines) < 6:
                    continue

                # Extração de data na linha 4 (índice 3)
                match = re.search(r"(\d{2}/\d{2}/\d{4})", lines[3])
                if not match:
                    continue
                current_date = match.group(1)
                pages_by_date.setdefault(current_date, {})

                # Limpeza de cabeçalho e rodapé
                content_lines = lines[4:]
                if len(content_lines) > 2:
                    content_lines = content_lines[:-2]

                # Filtrar linhas indesejadas
                unwanted = [
                    'SOULMV', 'Relatório de Mapa Cirúrgico', 'Data: ',
                    'GRUPO SÃO PIETRO', 'HOSPITAL BANCO DE OLHOS',
                    'MV | SoulMV',
                    'Cirurgia Lateralidade Convênio / Plano Sub-Plano Status Autorização',
                    'Hora Aviso Atend. Tipo Paciente Idade Telefone Leito UTI Rad. Prestador\\Atividade'
                ]
                content_lines = [l for l in content_lines if not any(u in l for u in unwanted)]

                # Agrupar por Centro Cirúrgico
                for line in content_lines:
                    if line.startswith("Centro Cirúrgico : "):
                        if current_block and buffer:
                            pages_by_date[current_date].setdefault(current_block, []).extend(buffer)
                        current_block = line.replace("Centro Cirúrgico : ", "").strip()
                        buffer = []
                    elif current_block:
                        buffer.append(line)

        # Flush último bloco
        if current_date and current_block and buffer:
            pages_by_date[current_date].setdefault(current_block, []).extend(buffer)

        return pages_by_date


class SalaSplitter(BaseProcessor):
    """
    Separa linhas de um bloco de centro cirúrgico em salas.

    Retorna mapa { sala_num: [linhas da sala] }.
    """

    def process(self, block_lines: List[str], prefix: str = "Sala : ") -> Dict[int, List[str]]:
        salas: Dict[int, List[str]] = {}
        current: Optional[int] = None
        buffer: List[str] = []

        for line in block_lines:
            if line.startswith(prefix):
                if current is not None:
                    salas[current] = buffer
                try:
                    # 'Sala : 24 - SALA 1' → 1
                    current = int(line.split()[-1])
                except ValueError:
                    current = -1
                buffer = []
            elif current is not None:
                buffer.append(line)

        if current is not None:
            salas[current] = buffer
        return salas


class SurgeryExtractor(BaseProcessor):
    """
    Extrai blocos de cirurgia e transforma em registros estruturados.
    """

    def process(self, sala_lines: List[str]) -> Dict[str, Dict[str, Any]]:
        blocks = self._extract_blocks(sala_lines)
        by_time = self._map_by_time(blocks)
        parsed: Dict[str, Dict[str, Any]] = {}
        for time, lines in by_time.items():
            parsed[time] = self._parse_block(time, lines)
        return parsed

    @staticmethod
    def _extract_blocks(lines: List[str]) -> List[List[str]]:
        blocks: List[List[str]] = []
        current: List[str] = []
        open_block = False
        for l in lines:
            if re.match(r"^\d{2}:\d{2}", l):
                if current:
                    blocks.append(current)
                current = [l]
                open_block = True
            elif open_block:
                current.append(l)
                if l.startswith("Tipo(s) de Anestesia:"):
                    blocks.append(current)
                    current = []
                    open_block = False
        if current:
            blocks.append(current)
        return blocks

    @staticmethod
    def _map_by_time(blocks: List[List[str]]) -> Dict[str, List[str]]:
        by_time: Dict[str, List[str]] = {}
        for blk in blocks:
            m = re.match(r"^(\d{2}:\d{2})", blk[0])
            key = m.group(1) if m else f"UNKNOWN_{len(by_time)}"
            by_time[key] = blk
        return by_time

    @staticmethod
    def _parse_block(time: str, lines: List[str]) -> Dict[str, Any]:
        # Base result
        result = {
            'time': time,
            'filename': None,
            'centro': None,
            'patient_name': None,
            'age': None,
            'phone': None,
            'surgeon': None,
            'anesthesist': None,
            'procedures': None,
            'anesthesia_type': None,
            'convenio': None,
            'observacao': None,
            'aviso': None,
            'tipo': None,
            'cod_paciente': None,
            'lines': lines
        }
        if not lines:
            return result

        # Tokens da primeira linha
        tokens = lines[0].split()
        # Identificar par Sim/Não
        sim_nao_pairs = {'Sim Sim', 'Sim Não', 'Não Sim', 'Não Não'}
        pair_idx = -1
        for i in range(len(tokens) - 1):
            if f"{tokens[i]} {tokens[i+1]}" in sim_nao_pairs:
                pair_idx = i
                break

        if pair_idx >= 0:
            result['aviso'] = tokens[1]
            result['tipo'] = tokens[2]
            result['cod_paciente'] = tokens[3]
            # Surgeon após par Sim/Não
            result['surgeon'] = ' '.join(tokens[pair_idx+2:])
            # Extrair nome, idade e telefone
            name_tokens: List[str] = []
            age: Optional[int] = None
            phone_tokens: List[str] = []
            for j in range(4, pair_idx):
                tok = tokens[j]
                if tok.isdigit() and age is None:
                    age = int(tok)
                elif age is None:
                    name_tokens.append(tok)
                else:
                    phone_tokens.append(tok)
            result['patient_name'] = ' '.join(name_tokens) or None
            result['age'] = age
            result['phone'] = ' '.join(phone_tokens) or None

        # Observação
        for line in reversed(lines):
            if line.startswith("Observação:"):
                result['observacao'] = line.replace("Observação:", "").strip()
                break
        # Tipo de anestesia
        for line in reversed(lines):
            if line.startswith("Tipo(s) de Anestesia:"):
                result['anesthesia_type'] = line.replace("Tipo(s) de Anestesia:", "").strip()
                break

        laterality_keywords = ['Esquerda', 'Direita', 'Bilateral', 'Não Se Aplica']
        unwanted_keywords = ['Observação:', 'DIREITO', 'ESQUERDO']
        # Procurar da parte inferior para cima, exceto a última linha
        for line in lines[::-1][1:-1]:
            if not any(k in line for k in laterality_keywords+unwanted_keywords):
                parts = line.split()
                if len(parts) == 1:
                    # único token: complemento de nome do paciente
                    result['patient_name'] = (result.get('patient_name') or '') + ' ' + parts[0]
                else:
                    # mais de um token: anestesista
                    result['anesthesist'] = line

        # Procedimentos e convênio
        procedures: List[str] = []
        status_keywords = ['Autorizado', 'Não Cadastrado']
        for line in lines:
            for kw in laterality_keywords:
                if kw in line:
                    before = line.split(kw)[0].strip()
                    procedures.append(before)
                    # Extrair convênio
                    try:
                        start = line.find(kw) + len(kw)
                        aft = line[start:].strip()
                        for st in status_keywords:
                            if st in aft:
                                result['convenio'] = aft.split(st)[0].strip()
                                break
                    except Exception:
                        pass
                    break
        if procedures:
            result['procedures'] = ' + '.join(sorted(procedures))

        return result


class InMemoryFlattener(BaseProcessor):
    """
    Achata a estrutura para { date: { room: { time: surgery_dict } } },
    injetando 'filename' e 'centro' em cada registro.
    """
    def process(self, content: Dict[str, Dict[str, Dict[str, List[str]]]]) -> Dict[str, Dict[int, Dict[str, Dict[str, Any]]]]:
        flattened: Dict[str, Dict[int, Dict[str, Dict[str, Any]]]] = {}
        for filename, dates in content.items():
            for date, centros in dates.items():
                flattened.setdefault(date, {})
                for centro, salas in centros.items():
                    for sala, surgeries in salas.items():
                        flattened[date].setdefault(sala, {})
                        for time, surgery in surgeries.items():
                            rec = surgery.copy()
                            rec['filename'] = filename
                            rec['centro'] = centro
                            flattened[date][sala][time] = rec
        return flattened


class ScheduleReorderer(BaseProcessor):
    """
    Ordena datas, salas e horários.
    """
    def process(self, data: Dict[str, Dict[int, Dict[str, Dict[str, Any]]]]) -> OrderedDict:
        ordered: OrderedDict = OrderedDict()
        for date in sorted(data.keys(), key=lambda d: datetime.strptime(d, '%d/%m/%Y')):
            ordered[date] = OrderedDict()
            for room in sorted(data[date].keys()):
                ordered[date][room] = OrderedDict()
                for t in sorted(data[date][room].keys(), key=lambda tm: datetime.strptime(tm, '%H:%M')):
                    ordered[date][room][t] = data[date][room][t]
        return ordered


class DurationCalculator(BaseProcessor):
    """
    Calcula duration_minutes com base no próximo horário.
    """
    def process(self, ordered: OrderedDict) -> OrderedDict:
        for date, rooms in ordered.items():
            for room, slots in rooms.items():
                times = list(slots.keys())
                for i, t in enumerate(times):
                    start_dt = datetime.strptime(t, '%H:%M')
                    if i + 1 < len(times):
                        next_dt = datetime.strptime(times[i+1], '%H:%M')
                        minutes = (next_dt - start_dt).total_seconds() / 60
                    else:
                        minutes = None
                    slots[t]['duration_minutes'] = minutes
        return ordered


class ShiftWeekdayAnnotator(BaseProcessor):
    """
    Serviço que adiciona 'turno' e 'weekday' a cada cirurgia,
    baseado em seu horário e data.
    """
    # Mapeamento de weekday() → nome em PT-BR
    WEEKDAY_MAP = {
        0: "2 - Segunda-feira",
        1: "3 - Terça-feira",
        2: "4 - Quarta-feira",
        3: "5 - Quinta-feira",
        4: "6 - Sexta-feira",
        5: "7 - Sábado",
        6: "1- Domingo",
    }

    def process(self, ordered: "OrderedDict[str, Dict[int, Dict[str, Any]]]") \
            -> "OrderedDict[str, Dict[int, Dict[str, Any]]]":
        """
        Para cada cirurgia em ordered[date][room][time], injeta:
          - 'turno': Manhã / Tarde / Noite
          - 'weekday': dia da semana em PT-BR
        """
        for date_str, rooms in ordered.items():
            # converte string 'dd/mm/YYYY' para objeto date
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            weekday = self.WEEKDAY_MAP[date_obj.weekday()]

            for room, slots in rooms.items():
                for time_str, surgery in slots.items():
                    # converte 'HH:MM' para objeto time
                    t = datetime.strptime(time_str, "%H:%M").time()

                    # define turno
                    if t < time(12, 0):
                        turno = "1 - Manhã"
                    elif t < time(17, 0):
                        turno = "2 - Tarde"
                    else:
                        turno = "3 - Noite"

                    # injeta no dict
                    surgery["turno"] = turno
                    surgery["weekday"] = weekday

        return ordered


class DataFrameSerializer(BaseProcessor):
    """
    Constrói DataFrame, salva CSV e retorna o DataFrame.
    """
    def process(self, duration_dict: OrderedDict, path: str = 'escala_bloco.csv') -> pd.DataFrame:
        records: List[Dict[str, Any]] = []
        for date, rooms in duration_dict.items():
            for room, slots in rooms.items():
                for time, surgery in slots.items():
                    rec = surgery.copy()
                    rec['date'] = date
                    rec['room'] = room
                    rec['time'] = time
                    records.append(rec)
        df = pd.DataFrame(records)
        desired_order = [
            'filename','centro',
            'date', 'weekday',
            'room','turno', 'time', 
            'surgeon','duration_minutes','procedures','anesthesia_type','convenio',
            'observacao','anesthesist',
            'patient_name','age','phone',
            'aviso','tipo','cod_paciente','lines'
        ]
        cols = [c for c in desired_order if c in df.columns]
        df = df[cols]
        df.to_csv(path, index=False)
        return df


class InsightsGenerator(BaseProcessor):
    """
    Gera relatórios de procedimentos e procedimentos com duração.
    """
    def process(self, df: pd.DataFrame) -> None:
        # Procedimentos por cirurgião
        df_u1 = df.drop_duplicates(subset=['surgeon','procedures','anesthesia_type','duration_minutes'])
        lines: List[str] = []
        for surgeon, grp in df_u1.groupby('surgeon'):
            lines.append(f"Dr(a) {surgeon}:")
            for _, row in grp.iterrows():
                dur = row['duration_minutes']
                dur_text = f"{int(dur)} minutos" if pd.notna(dur) else "quanto tempo"
                anesth = row['anesthesia_type'] or ''
                anesth_text = f"sob anestesia {anesth}" if anesth else ''
                lines.append(f"  Realiza o procedimento {row['procedures']} {anesth_text} em {dur_text}?")
            lines.append("")
        with open('procedimentos.txt','w',encoding='utf-8') as f:
            f.write("\n".join(lines))
        # Procedimentos por tipo
        df_u2 = df.drop_duplicates(subset=['procedures','anesthesia_type','duration_minutes'])
        lines2: List[str] = []
        for i, ((proc, anes), grp) in enumerate(df_u2.groupby(['procedures','anesthesia_type'])):
            lines2.append(f"{i}. {proc} sob {anes}:")
            for _, row in grp.iterrows():
                dur = row['duration_minutes']
                dur_text = f"{int(dur)} minutos" if pd.notna(dur) else "quanto tempo"
                lines2.append(f"  O procedimento {row['procedures']} leva {dur_text}?")
            lines2.append("")
        with open('procedimentos_duracao.txt','w',encoding='utf-8') as f:
            f.write("\n".join(lines2))


class ScheduleController:
    """
    Orquestra todos os passos do pipeline:
    Parser → Splitter → Extractor → Flattener → Reorderer → Duration → Serializer → Insights
    """
    def __init__(self, pdf_dir: str):
        self.parser = PDFScheduleParser(pdf_dir)
        self.splitter = SalaSplitter()
        self.extractor = SurgeryExtractor()
        self.flattener = InMemoryFlattener()
        self.reorderer = ScheduleReorderer()
        self.durationer = DurationCalculator()
        self.annotator  = ShiftWeekdayAnnotator()
        self.serializer = DataFrameSerializer()
        self.insights = InsightsGenerator()

    def run(self) -> None:
        # 1) Extrair conteúdo bruto
        raw = self.parser.process()
        # 2) Split por sala e extrair cirurgias
        for filename, dates in raw.items():
            for date, centros in dates.items():
                for centro, lines in centros.items():
                    salas = self.splitter.process(lines)
                    parsed_salas: Dict[int, Dict[str, Dict[str, Any]]] = {}
                    for sala, sala_lines in salas.items():
                        parsed_salas[sala] = self.extractor.process(sala_lines)
                    raw[filename][date][centro] = parsed_salas
        # 3) Achatar estrutura
        flat = self.flattener.process(raw)
        # 4) Ordenar datas, salas e horários
        ordered = self.reorderer.process(flat)
        # 5) Calcular durações
        durationed = self.durationer.process(ordered)
        # 6) ANOTAR TURNO e WEEKDAY
        annotated = self.annotator.process(durationed)
        # 7) Serializar em DataFrame e CSV
        df = self.serializer.process(annotated)
        # 8) Gerar insights
        self.insights.process(df)
        df.to_csv('escala_bloco.csv', index=False)
        return df


if __name__ == '__main__':
    controller = ScheduleController(r'D:\Fausto Stangler\Documentos\Python\BFX\pdf')
    df = controller.run()
    print('done!')