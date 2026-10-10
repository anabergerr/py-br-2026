# Roteiro de fala

Acompanha o `index.html`, na ordem. Setas ou espaço trocam o slide.

**Convenção:**
- O texto corrido de cada seção é o que você **fala** — suas falas, palavra a palavra.
- Os blocos **Ao vivo** e **Código, linha a linha** são **referência**, não são falados. "Ao vivo" é o comando de terminal pra rodar na hora; "Código, linha a linha" é o gabarito do código que está na tela, pra você não travar se alguém perguntar o que cada linha faz.

Estrutura: problema primeiro, solução depois. O GIL entra como segredo (explica a vitória do ViaCEP) e só depois vira o vilão (trava o carimbo). Conceito no momento que usa — nada de bloco teórico na abertura.

Antes de subir: `index.html` aberto, e dois terminais na pasta `threads-demo`.

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv-ft\Scripts\python.exe -c "import sys; print(sys._is_gil_enabled())"
```

O segundo tem que imprimir `False`.

---

## 1 — Apresentação

"Olá! Eu sou [seu nome], [cargo / time / onde trabalha]. Me acha em [github · linkedin]."

## 2 — Capa

"Todo mundo aqui já adicionou threads achando que ia acelerar um programa. E aí acontece uma coisa meio esquisita: às vezes acelera de verdade, às vezes não muda nada. Esta palestra é sobre esse 'às vezes' — quando thread ajuda e quando é só ilusão. Vou contar com dois exemplos: uma planilha de CEPs que acelera, e um carimbo de arquivo que não acelera. A diferença entre os dois é a palestra."

## 3 — O problema

"Caiu no meu colo uma planilha com milhares de clientes, cada linha com um CEP, e eu precisava da rua, do bairro e da cidade de todos. Cada linha vira uma chamada HTTPS de verdade na API do ViaCEP — não tem sleep simulando a rede. Uma linha não depende da outra. Se eu faço uma por vez, o tempo total é a soma de todas as esperas. Tudo isso roda num processo só, o script, com uma thread, uma linha de trabalho."

## 4 — Sequencial

"O laço é o garçom, uma ação por vez. Para cada linha, a função lookup_cep manda o HTTPS e fica parada até o JSON voltar. A próxima ação espera a anterior terminar."

**Ao vivo**

```powershell
python src/main.py sequencial --limit 20
```

"No log fica Iniciando, Finalizando, Iniciando, Finalizando — nunca dois Iniciando seguidos. O tempo total fica no final. Guardem esse número: é a baseline que o próximo slide derruba."

**Observação de CPU (fala opcional, se estiver com o monitor aberto):** "Reparem no uso de CPU enquanto roda. Ele dá uma pequena estressada e logo volta — fica em torno de 33%, com picos até 75%, mas nunca sustenta. Isso é a dica visual de que a CPU não é o gargalo: a thread passa quase todo o tempo parada esperando a rede responder. O processo tá ali, mas de braços cruzados."

**Código, linha a linha:**

- `for row in rows:` — percorre cada linha da planilha, uma de cada vez.
- `looked_up = lookup_cep(row["cep"])` — pega o CEP da linha e chama o ViaCEP. É aqui que bloqueia: a thread fica parada até o JSON voltar (o comentário `# bloqueia aqui` marca o ponto).
- `results.append({...})` — monta o resultado com o `id` da linha e o endereço formatado, e guarda na lista. Só depois disso o laço vai pra próxima linha.

## 5 — Conceitos

"Antes de ligar mais threads, três palavras rápidas pra todo mundo estar no mesmo vocabulário. Processo: é o script rodando — ele tem seu próprio Python e seu próprio GIL. Thread: é uma linha de trabalho dentro do processo; as threads de um processo compartilham a mesma memória. Várias threads, um processo, um GIL. Núcleo: é a unidade da CPU que executa de verdade; vários núcleos significa vários que rodam ao mesmo tempo. Até agora a demo rodou com 1 processo e 1 thread. O próximo slide liga mais threads dentro do mesmo processo — e aí a gente vê se acelera."

## 6 — Threads

"O mesmo trabalho, agora com várias threads. ThreadPoolExecutor com 10 workers, e o map entrega cada linha para _lookup. São 10 workers, ou seja, 10 threads — todas dentro do mesmo processo. As 20 linhas da planilha são 20 tarefas: as 10 threads pegam as 20 linhas, uma por vez cada; quando uma termina uma linha, pega a próxima. Em qualquer instante, 10 linhas rodam juntas, uma por thread. O map devolve o resultado na ordem do CSV."

**Ao vivo**

```powershell
python src/main.py threads --limit 20 --workers 10
```

"Agora aparecem vários Iniciando antes do primeiro Finalizando. worker_0, worker_1: cada um pegou uma linha. Compara o tempo total com o do slide anterior. Acelerou. Mas eu não vou explicar ainda por quê — esse é o próximo slide."

**Observação de CPU (fala opcional):** "De novo o monitor de CPU: agora com várias threads, ele continua baixo — 29, 33%, no máximo 40%. Não chega a estressar. Isso é legal de ver porque confirma o ponto: mesmo com várias threads, a CPU tá ociosa esperando a rede. O ganho aqui não veio de mais núcleo — veio de sobrepor as esperas."

**Código, linha a linha:**

- `from concurrent.futures import ThreadPoolExecutor` — importa o pool de threads da biblioteca padrão (nada de `pip install`).
- `with ThreadPoolExecutor(max_workers=10) as executor:` — cria 10 threads operárias. O `with` garante que o pool espere todo mundo terminar antes de seguir.
- `results = list(executor.map(_lookup, rows))` — entrega cada linha da planilha pra um worker processar. O `map` dispara as chamadas em paralelo e devolve os resultados na ordem do CSV (não na ordem em que chegam — o log mostra a ordem real de chegada).

**Sobre a biblioteca:** a estrela aqui é a `concurrent.futures`, da biblioteca padrão — é ela que cria o pool de threads (e, no slide 9, o pool de processos). Nada de `pip install`: a HTTP é `urllib.request` (não a `requests`), o carimbo é `hashlib`, o lock do log é `threading`. Tudo stdlib. A `concurrent.futures` serve pra entregar um monte de tarefas independentes a um pool e esperar todo mundo terminar, sem você gerenciar as threads na mão.

## 7 — Por que acelerou?

"Por que acelerou? Imagina o GIL como um bastão no centro da sala: só quem está com o bastão roda Python. A thread A pega o bastão, manda o HTTPS, e como vai ficar parada esperando a rede, devolve o bastão — não precisa dele enquanto espera. A thread B pega o bastão e dispara a chamada dela. As duas estão esperando a internet ao mesmo tempo, mas o bastão só passa por uma mão de cada vez. A rede fica ocupada junta. O Python segue revezando um núcleo só. A animação na tela é o garçom único revezando as quatro mesas. Continua sendo um garçom: o Python reveza um núcleo, e quem anda junto é a rede. O nome disso é concorrência. O GIL continua ali — ele só não segura a thread durante a espera. E é esse 'durante a espera' que o próximo slide tira."

**Pergunta comum:** "Mas e se a planilha tiver MUITO dado, tipo um milhão de linhas — mais núcleos ajudam?" A resposta curta é: em geral não, e o motivo é o mesmo de sempre. No I/O o gargalo é a espera da rede, não a sua CPU. Mais núcleos ficam ociosos esperando do mesmo jeito. O que ajuda é mais threads — mais chamadas em voo ao mesmo tempo — até onde a API (ou a sua banda) aguenta. Depois disso, mais thread ou mais núcleo só gera erro de limite (429) ou enfileira. Mais núcleos só passam a ajudar se entrar trabalho de CPU no meio — tipo processar/transformar a resposta pesado, ou gravar em disco num ritmo que a um núcleo não dá conta de acompanhar. Só I/O puro, com resposta leve? Um núcleo basta; o limite é a rede, não você.

## 8 — A pegadinha

"E se não houver espera nenhuma? No ViaCEP a thread ganhava tempo porque ficava parada esperando a rede. Tira a rede. A ação trocou: em vez de buscar um CEP, cada thread carimba um bloco. Carimbar é gerar o SHA-256 do conteúdo — um código curto que identifica o arquivo. Mesmo conteúdo gera o mesmo código; mudou 1 byte, o código muda. Na vida real, serve pra conferir se um arquivo chegou inteiro: compara o carimbo de quem enviou com o do que chegou. Aqui a gente não confere arquivo de verdade — o hash_blocks carimba centenas de milhares de bloquinhos de 1024 bytes. O tamanho é de propósito: o hashlib só solta o GIL a partir de 2048 bytes; abaixo disso, a trava fica presa. E aqui está o ponto: a CPU trabalha o tempo inteiro, sem nenhuma espera de rede. Então a thread nunca devolve o bastão. As mesmas threads, o mesmo ThreadPool, vão acelerar de novo, certo?"

**Código, linha a linha:**

- `import hashlib` — importa a biblioteca padrão que faz o SHA-256.
- `# 1024 bytes < 2048: hashlib não solta o GIL` — o comentário é o truque da demo: o `hashlib` só solta o GIL pra blocos grandes (≥2048 bytes). Com 1024, a trava fica presa dentro da própria chamada do `sha256`.
- `for i in range(start, end):` — carimba cada bloco do pedaço que essa thread pegou.
- `payload = i.to_bytes(8, "big") * 128` — inventa 1024 bytes a partir do índice `i` (8 bytes repetidos 128 vezes). É o "conteúdo" do bloco — não veio de arquivo, veio do contador.
- `total += hashlib.sha256(payload).digest()[0]` — carimba o bloco (SHA-256), pega o 1º byte do carimbo e soma. A CPU faz isso o tempo inteiro — não tem espera, então o GIL nunca solta.

## 9 — Decepção + processos

"A decepção primeiro. Nesse carimbo, com o GIL ligado, o ThreadPoolExecutor é o um garçom. Várias threads, um processo, um GIL. Elas se revezam no mesmo núcleo. O tempo empata com o sequencial. A thread nunca devolve o bastão — a CPU não para nunca, então não tem espera pra devolver. O vilão revelado: o mesmo segredo que salvou o ViaCEP agora trava o carimbo. A solução é o ProcessPoolExecutor: os quatro garçons. Cada worker é outro processo, com seu Python e seu GIL. Quatro workers podem ocupar quatro núcleos ao mesmo tempo. Aí o ganho aparece. A animação na tela é o paralelismo: 4 garçons, 4 núcleos — só com processo. Um processo é outro Python, outro GIL, outro núcleo possível."

**Ao vivo, no Python com GIL**

```powershell
.\.venv\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4
```

"A primeira linha diz que o GIL está ligado. A leitura no final: threads perto de 1x, processos na frente. A decepção e a solução, no mesmo comando."

## 10 — Sem o GIL

"E se tirassem a trava? O slide anterior precisou de processo pra ganhar núcleo, driblando o GIL por fora. E se a gente pudesse tirar o GIL por dentro? Desde o 3.13 existe um build sem a trava: python3.13t, free-threaded. No 3.13 era experimental; a partir do 3.14 é oficialmente suportado — mas ainda opcional, não é o default. É o mesmo ThreadPoolExecutor e o mesmo hash_blocks. Sem o GIL, aquelas threads deixam de ser o garçom único e passam a ocupar vários núcleos. Bibliotecas em C ainda podem ter atrito nesse build; essa demo usa só a biblioteca padrão. A checagem é sys._is_gil_enabled(), e aqui ela devolve False."

**Código, linha a linha:**

- `import sys` — importa o módulo `sys`, que dá acesso ao estado do interpretador.
- `sys._is_gil_enabled()` — pergunta pro Python se o GIL tá ligado. No `.venv-ft` devolve `False`; no `.venv` devolve `True`. É a checagem que confirma qual build tá rodando, sem adivinhar.

**Ao vivo, no free-threaded**

```powershell
.\.venv-ft\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4
```

"Mesmo comando do slide anterior. Desta vez as threads aceleram. A animação dos 4 garçons, que no slide 9 só acontecia com processo, agora acontece com thread também."

## 11 — Free-threaded em 2026

"Isso não é futuro distante, é agora. A linha do tempo: 3.13, outubro de 2024, o build sem GIL entra, ainda experimental — é a fase I do PEP 703. 3.14, outubro de 2025, deixa de ser experimental: o PEP 779 remove o rótulo e o build vira oficialmente suportado, fase II. Ainda opcional, não é o default. A performance também melhorou: o specializing interpreter foi ligado no free-threaded e a penalidade no single-threaded caiu pra uns 5 a 10 por cento. 3.15, outubro de 2026, saiu agora: traz a Stable ABI abi3t pra free-threaded, o que facilita pacotes de extensão C. No macOS, os binários oficiais já instalam free-threading por padrão. A fase III, virar o default, ainda é indecidida — depende do ecossistema de extensões C pegar o abi3t. A mensagem pra casa: não é mais experimental desde o 3.14, mas ainda é opcional."

## 12 — Medido

"Os dois exemplos, dois Pythons — agora na mesma tabela. As linhas de cima são o CEP, as de baixo são o carimbo. No CEP, o free-threaded não dá ganho — e aqui tem um detalhe que surpreende: ele pode até atrapalhar. Com o GIL ligado, o sequencial faz 26,33s e as threads caem pra 15,50s — speedup de 1,70x, as threads ajudam. Sem o GIL, o sequencial fez 14,18s e as threads subiram pra 18,98s — speedup de 0,75x, ou seja, mais lento que o sequencial. Por que isso? Remover o GIL não traz benefício pra tarefa de I/O: o Python padrão já libera o GIL naturalmente durante a espera da rede. Sem o GIL, as threads passam a rodar de verdade em paralelo — mas o gargalo é a rede, não a CPU, então esse paralelismo a mais só gera overhead, sem ganho. E reparem nos tempos absolutos do sequencial: 26,33s num build, 14,18s no outro. Essa oscilação não é do Python — é da rede e da API, que respondem diferente a cada execução. E é justamente isso que confirma a tese: o gargalo é a conectividade, não o processamento.

No carimbo, a história é outra. Com o GIL ligado: sequencial 2,87s; threads 2,75s, 1,05x — um núcleo só, as threads mal mexem; processos 1,12s, 2,57x. Sem o GIL: sequencial 2,88s — esse build tem um custo pequeno; as threads caem pra 0,80s, 3,62x; processos 1,07s, 2,71x. Com GIL, threads num núcleo só. Sem GIL, o ThreadPool ocupa vários núcleos. A tabela fecha o arco: o mesmo 'às vezes' da capa, agora explicado nos dois exemplos."

**Pra reproduzir as linhas do CEP (rode e anote):**

```bash
# CEP nos dois builds, lado a lado (sequencial + threads em cada um)
python src/main.py comparar_cep --limit 200 --workers 2
```

Cada build imprime `Tempo sequencial`, `Tempo com Threads` e o `Speedup`. Os tempos absolutos oscilam entre execuções (rede/API), mas o sinal é o speedup dentro de cada build: com GIL as threads ajudam (1,70x), sem GIL elas não ajudam — e podem atrapalhar (0,75x). O ponto didático: free-threaded não ajuda no I/O, e a oscilação dos tempos é a prova de que o gargalo é a rede.

**As linhas do carimbo** já estão preenchidas como referência; pra medir na hora, é o `cpu` nos dois venvs (slides 9 e 10).

## 13 — Três ideias

"Três ideias pra levar pra casa. Primeira: I/O-bound, a planilha — threads já ajudam hoje, porque a espera solta o GIL. É o um garçom, com a rede andando junta. Segunda: CPU-bound com GIL, o carimbo — o ThreadPool fica num núcleo só; quem usa os outros núcleos é o processo, um garçom por núcleo. Terceira: free-threaded — o mesmo ThreadPool finalmente ocupa vários núcleos. E a regra de bolso, que responde a pergunta mais comum: 'então minhas threads rodam em núcleos diferentes?'. Com o GIL, não: thread não espalha em núcleos, quem espalha é processo. Sem o GIL, sim, a thread também espalha. E cuidado com uma pegadinha: no I/O a thread acelera sem espalhar em núcleo nenhum — ali o ganho é a espera de rede se sobrepondo, não núcleo extra."

## 14 — Perguntas

"O código está no repositório. A parte de CEP é o ViaCEP. A parte de CPU é o comando cpu. A comparação é a pasta .venv contra a .venv-ft. Perguntas?"

## 15 — Créditos

"Créditos: a arte é do [nome do seu amigo]. A demo e o código são meus. A API é o ViaCEP. Obrigada!"

---

## Se sobrar tempo

Os dois tempos do ViaCEP e o speedup, numa execução só:

```powershell
python src/main.py comparar --limit 20 --workers 10
```

Uma chamada só, para mostrar o endereço voltando:

```powershell
python src/main.py uma
```

## Se a rede falhar

O `cpu` não depende do ViaCEP. Segue do slide 8. A tabela do slide 12 fecha o argumento sem chamar a API.
