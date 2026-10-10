# Threads e planilha: espera de API, não CPU

Demo de palestra. O programa enriquece CEPs de uma planilha com a API pública
do [ViaCEP](https://viacep.com.br) e mede a diferença entre fazer isso **uma
por vez** e fazer isso **com várias threads**.

Material pronto para slides: [`docs/SLIDES.md`](docs/SLIDES.md).

Cada linha é uma chamada HTTPS real. Não há `time.sleep()` no lugar da API.

## O problema

Havia um lote grande de clientes com CEP. Cada linha precisava de uma consulta
externa para preencher rua, bairro e cidade. O código esperava a resposta da
linha atual antes de enviar a próxima.

Esse desenho está certo quando a próxima etapa depende da anterior. Aqui as
linhas são independentes. O tempo total virava a soma das esperas.

## Como essa demo se relaciona com um caso real

Cada linha do CSV é uma tarefa independente que precisa esperar um serviço
externo. Na vida real: enriquecer planilha, validar links, baixar anexos,
consultar CEP/CNPJ. Nesta demo, o serviço é o ViaCEP.

O Python quase não calcula nada: monta a URL, envia um HTTPS e fica parado até
o JSON voltar. Esse tempo parado é o que muda quando várias chamadas viajam ao
mesmo tempo.

## O que é I/O-bound

Um trabalho é **I/O-bound** quando o limite é entrada e saída, não a CPU.
Disco, banco, rede e API entram aqui.

Nesta demo, o I/O é a resposta do ViaCEP. A thread pede o endereço e fica
bloqueada no socket até o servidor responder. A CPU local fica ociosa durante
essa espera.

## I/O-bound e CPU-bound

| | I/O-bound | CPU-bound |
| --- | --- | --- |
| O tempo vai para | esperar rede, disco ou outro processo | calcular aqui na máquina |
| Exemplo | esta consulta ViaCEP | loop numérico pesado em Python puro |
| Threads ajudam? | sim, quando as esperas podem se sobrepor | em geral não, no CPython, por causa do GIL |
| Caminho usual | `ThreadPoolExecutor` ou asyncio | `ProcessPoolExecutor`, processos, ou código nativo |

`asyncio` também serve para muitas esperas de rede, com uma thread só. Esta
palestra mostra threads porque o código de bloqueio continua sendo o código
síncrono normal: chamar a função e esperar o retorno.

## Processamento sequencial

`src/sequential.py` faz isto, para cada CEP:

1. envia para o ViaCEP;
2. espera a resposta;
3. guarda o endereço na lista;
4. só então passa para a próxima.

O log nunca mostra dois `Iniciando` seguidos sem um `Finalizando` no meio.

O tempo total fica perto da soma das latências.

## Processamento concorrente

`src/threaded.py` entrega o mesmo trabalho a um `ThreadPoolExecutor`. Várias
threads podem estar paradas na API ao mesmo tempo.

Se aparecerem vários `Iniciando` antes do primeiro `Finalizando`, as chamadas
estão sobrepostas. O nome `worker_0`, `worker_1`, … mostra qual thread pegou
qual linha.

O `executor.map` devolve os resultados na ordem do CSV. Os logs não seguem
essa ordem. Eles seguem a ordem em que as respostas chegam.

```
Sequencial   [----1----][----2----][----3----][----4----]

4 threads    [----1----]
             [----2----]
             [----3----]
             [----4----]
```

O desenho de baixo termina perto da duração da chamada mais lenta do grupo,
mais um pouco de overhead. Não perto da soma.

## Como o ThreadPoolExecutor funciona

O pool é um conjunto fixo de threads operárias.

1. Você escolhe `max_workers`.
2. Entrega as linhas com `map`.
3. Cada worker pega um CEP, chama `lookup_cep` e, ao terminar, pega outro se
   ainda houver.
4. O `with` espera todo mundo terminar e devolve as threads.

Dez workers e vinte linhas não significam vinte threads. Significam dez
threads. Assim que uma termina, ela pega a próxima da fila.

A função `log()` em `viacep_client.py` segura um `Lock` só na hora de escrever
a linha no terminal, para dois workers não misturarem o texto no meio. A
chamada ao ViaCEP fica de fora do lock. Se a chamada estivesse dentro do lock,
a concorrência sumiria.

## O GIL, e por que ele não impede o caso ViaCEP

O **GIL** (Global Interpreter Lock) do CPython deixa uma thread por vez
executar bytecode Python. Por isso threads não aceleram um loop pesado escrito
em Python puro.

Quando a thread entra numa espera de rede, a história muda. A leitura do
socket solta o GIL enquanto o sistema operacional espera os bytes. Outra
thread pode rodar e iniciar outro HTTPS.

O GIL continua existindo. Ele só não fica segurando a thread durante a espera
da API. Várias requisições ficam em voo ao mesmo tempo.

## Demo do GIL: CPU com e “sem” GIL

Há dois contrastes na palestra:

### A) Com GIL (Python normal) — threads vs processos

O mesmo cálculo pesado em Python puro (contar primos):

```powershell
python src/main.py cpu
python src/main.py cpu --upto 800000 --workers 4
```

| Modo | Expectativa com GIL ligado |
| --- | --- |
| Sequencial | baseline |
| Threads | tempo parecido com o sequencial |
| Processos | bem mais rápido (cada processo tem seu GIL) |

O comando imprime se o GIL está ligado e uma leitura automática dos tempos.

Isso não remove o GIL do interpretador: **contorna** com processos. É o jeito
estável de mostrar o efeito do GIL no dia a dia.

### B) Sem GIL de verdade — Python free-threaded

No Python 3.13+ existe build **free-threaded** (sem GIL). Rode o **mesmo**
`cpu` nos dois interpretadores e compare.

Neste repo o free-threaded **já foi instalado** nesta máquina e o processo está
documentado em [`docs/FREE_THREADED.md`](docs/FREE_THREADED.md). Para repetir:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_free_threaded.ps1
```

#### Rodar a mesma demo nos dois

```powershell
# COM GIL — threads ≈ sequencial
.\.venv\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4

# SEM GIL — threads tendem a acelerar
.\.venv-ft\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4
```

Expectativa didática (medida aqui neste setup):

| Build | Threads no `cpu` | Processos no `cpu` |
| --- | --- | --- |
| CPython com GIL (`.venv`) | ~1x (quase sem ganho) | ganho claro |
| Free-threaded (`.venv-ft`) | ~2–3x | também ganha |

O ViaCEP (`comparar`) continua acelerando com threads **nos dois** builds,
porque o gargalo é rede, não o GIL.

## Por que mais threads não significam mais velocidade

Mais workers deixam de ajudar quando:

- já há chamadas suficientes em voo para preencher a espera;
- a API limita concorrência ou responde erro;
- erros disparam nova tentativa dentro de `lookup_cep`;
- o overhead de acordar threads passa a aparecer num lote pequeno.

Um tempo menor com muitos erros não é vitória. A tabela do benchmark mostra a
coluna `Erros` por isso.

```text
speedup = tempo_sequencial / tempo_threaded
```

## ViaCEP

API pública, sem chave:

```text
GET https://viacep.com.br/ws/{cep}/json/
```

A função `lookup_cep(cep)` devolve logradouro, bairro, localidade e UF. Se o
CEP não existir, a API responde com `"erro": true`.

Se a rede falhar ou vier `429`/`5xx`, a mesma linha é tentada de novo, no
máximo 3 vezes, com espera de 1s e 2s. Essa espera acontece dentro da thread
que pegou a linha. As outras continuam.

## Como executar

Requer Python 3.10 ou superior. Sem dependências externas.

```powershell
cd threads-demo
python -m venv .venv
.venv\Scripts\Activate.ps1
python src/generate_data.py
python src/main.py uma
```

`generate_data.py` aceita a quantidade:

```powershell
python src/generate_data.py --count 100
python src/generate_data.py --count 200
```

O padrão desse gerador é 100. Os CEPs são públicos reais, intercalados de
várias cidades.

### Roteiro da palestra

1. O problema. Mostre uma linha de `data/ceps.csv` e explique que cada linha
   espera uma API externa.
2. O sequencial. Abra `src/sequential.py` e mostre o `for`.
3. O tempo. Rode o lote.

```powershell
python src/main.py sequencial --limit 20
```

4. As threads. Abra `src/threaded.py` e mostre `_lookup` e o `ThreadPoolExecutor`.
5. O concorrente. Vários `Iniciando` antes de um `Finalizando`.

```powershell
python src/main.py threads --limit 20 --workers 10
```

6. O novo tempo. Está no final desse comando.
7. O contraste do GIL (CPU).

```powershell
python src/main.py cpu
```

Explique: no ViaCEP threads ajudam (I/O); no `cpu` threads quase não (GIL);
processos ajudam. Se tiver Python free-threaded, rode o mesmo `cpu` nele e
mostre threads acelerando de verdade.

8. O benchmark ViaCEP, se quiser.

```powershell
python src/main.py benchmark --limit 20
```

Para fechar ViaCEP com os dois tempos e o speedup numa execução só:

```powershell
python src/main.py comparar --limit 20 --workers 10
```

Antes de tudo isso, valide a integração com uma chamada:

```powershell
python src/main.py uma
```

Saída esperada:

```text
Endereço: ...
Tempo: ... segundos
```

## Estrutura

```text
threads-demo/
├── data/
│   └── ceps.csv
├── docs/
│   └── FREE_THREADED.md    # instalação do Python sem GIL
├── scripts/
│   └── install_free_threaded.ps1
├── src/
│   ├── generate_data.py    # CSV com CEPs
│   ├── viacep_client.py    # uma chamada ao ViaCEP
│   ├── sequential.py       # laço, uma por vez
│   ├── threaded.py         # ThreadPoolExecutor
│   ├── cpu_bound.py        # sequencial vs threads vs processos (GIL)
│   ├── benchmark.py        # 1, 2, 5, 10, 20 workers
│   └── main.py             # comandos da palestra
├── .venv/                  # Python normal (GIL ligado)
├── .venv-ft/               # Python free-threaded (GIL desligado)
├── .gitignore
├── requirements.txt
└── README.md
```

Rode os comandos a partir de `threads-demo`. Os imports usam a pasta `src/`
porque é o diretório do script. Os caminhos do CSV saem de `__file__`, então o
diretório atual pode ser outro.
