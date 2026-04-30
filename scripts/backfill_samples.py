# scripts/backfill_samples.py

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para encontrar o módulo beatforge
sys.path.append(str(Path(__file__).parent.parent))

from beatforge.sampler import Sampler

def backfill():
    sampler = Sampler()
    # Pastas para buscar mp3 existentes
    target_dirs = ["music", "Music 120", "Music 160"]
    
    count = 0
    for d in target_dirs:
        path = Path(d)
        if not path.exists():
            print(f"Diretório não encontrado: {d}")
            continue
        
        print(f"Buscando em {d}...")
        for file in path.rglob("*.mp3"):
            # Ignora arquivos que já são samples
            if file.name.endswith("_sample.mp3"):
                continue
            
            # Define o caminho do sample
            sample_path = file.with_name(f"{file.stem}_sample.mp3")
            
            # Se o sample não existe, cria
            if not sample_path.exists():
                print(f"Gerando sample para: {file.name}")
                try:
                    sampler.create_sample(file)
                    count += 1
                except Exception as e:
                    print(f"Erro ao processar {file.name}: {e}")
            else:
                # Opcional: print('.', end='', flush=True) para progresso silencioso
                pass
    
    print(f"\nConcluído! {count} novos samples gerados.")

if __name__ == "__main__":
    backfill()
