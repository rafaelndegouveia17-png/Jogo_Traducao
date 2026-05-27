# Jogo_Traducao
# LinguaVox

LinguaVox é um jogo de pronúncia e tradução em Python, onde você fala palavras ou frases em um idioma escolhido e tenta acertar a resposta para ganhar pontos.

## O que o projeto faz

- Escolha um idioma para praticar
- Escolha o nível de dificuldade
- Fale no microfone e receba reconhecimento de voz
- Compare sua pronúncia com a resposta esperada
- Acumule pontos e veja o ranking

## Requisitos

- Python 3.10+
- Microfone funcional
- Dependências do projeto

## Instalação

1. Clone ou baixe este projeto.
2. Abra a pasta do projeto no terminal.
3. Instale as dependências:

```bash
pip install sounddevice numpy scipy SpeechRecognition deep-translator
```

4. Execute o jogo:

```bash
python main.py
```

## Como usar

1. Digite seu nome.
2. Escolha o idioma.
3. Escolha o nível.
4. Fale a tradução no microfone.
5. Veja o resultado e continue jogando.

## Observações importantes

- O programa precisa de acesso ao microfone do sistema.
- Em alguns computadores Windows, o reconhecimento de voz pode exigir um driver de áudio atualizado ou um microfone configurado como dispositivo padrão.
- Se aparecer erro de áudio, teste o microfone no sistema antes de rodar o jogo.

## Estrutura do projeto

- `main.py` — aplicação principal
- `linguavox_ranking.json` — ranking salvo localmente

## Licença

Este projeto é para uso pessoal e educacional.
