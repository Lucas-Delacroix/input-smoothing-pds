# Input Smoothing PDS

Visualizador em tempo real de suavização de entrada (mouse) usando média móvel e suavização exponencial (IIR). Permite ajustar parâmetros no teclado e ligar/desligar o histórico para observar o efeito dos filtros.

## Pré-requisitos
- Python 3.10+ instalado.
- Dependências: pygame, numpy, matplotlib (instale via `pip` com o `requirements.txt`).

## Instalação e execução
1. (Opcional) Crie e ative um ambiente virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Rode o app:
   ```bash
   python3 src/main.py
   ```

## Controles
- `UP` / `DOWN`: aumenta/diminui o tamanho da janela da média móvel (N).
- `RIGHT` / `LEFT`: aumenta/diminui o fator `alpha` do filtro exponencial.
- `H`: liga/desliga o histórico; ao desligar, o histórico e o estado do filtro são limpos.
- `ESC` ou fechar a janela: sair.

## O que você vê na tela
- Linha vermelha: pontos brutos do mouse.
- Linha verde: média móvel dos pontos.
- Linha azul: suavização exponencial (IIR).
- Círculos indicam a posição atual de cada série; o HUD no canto mostra os parâmetros ativos.

## Arquitetura rápida
- `src/main.py`: laço principal, inicialização e orquestração.
- `src/ui.py`: entrada de usuário (teclas) e renderização.
- `src/input_device.py`: estruturas de dados e filtros (média móvel e IIR) com buffers.
- `src/filters.py`: funções puras de filtragem.
