# Roteiro de fala

Acompanha o `index.html`, na ordem. Setas ou espaço trocam o slide. O parágrafo é o que falar. O que está em **Ao vivo** é terminal — pode pular se o tempo apertar. A tabela do final já tem uma medição pronta.

Estrutura: problema primeiro, solução depois. O GIL entra como segredo (explica a vitória do ViaCEP) e só depois vira o vilão (trava o carimbo). Conceito no momento que usa — nada de bloco teórico na abertura.

Antes de subir: `index.html` aberto, e dois terminais na pasta `threads-demo`.

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv-ft\Scripts\python.exe -c "import sys; print(sys._is_gil_enabled())"
```

O segundo tem que imprimir `False`.

---

## 1 — Capa

Abre com o gancho da tela, no tom de quem já passou por isso: todo mundo já adicionou threads achando que ia acelerar. E aí: ou voou, ou não mudou nada. Pausa. Esta palestra é o porquê — quando thread ajuda e quando é só ilusão.

Não prometa teoria. Prometa uma história: uma planilha de CEPs que voa, e um carimbo de arquivo que não voa. A diferença entre os dois é a palestra.

## 2 — O problema

Começa pelo problema, não pelo conceito. Caiu no seu colo uma planilha com milhares de clientes, cada linha com um CEP, e você precisa da rua, do bairro e da cidade de todas. Cada linha é uma chamada HTTPS de verdade na API do ViaCEP. Não tem `sleep` no lugar da rede. Uma linha não depende da outra.

Uma por vez, o tempo total vira a soma de todas as esperas. É o garçom único, uma ação depois da outra. Deixa a dor aqui — o público precisa sentir o problema antes da solução.

A última frase da tela dá o único conceito que importa agora: tudo roda num processo só, o script, com uma thread, uma linha de trabalho. Não explique núcleo nem concorrência ainda. Chega na hora certa.

## 3 — Sequencial

O laço é o garçom, uma ação por vez. Para cada linha, `lookup_cep`. A função manda o HTTPS e fica parada até o JSON voltar. A próxima ação espera a anterior terminar.

**Ao vivo**

```powershell
python src/main.py sequencial --limit 20
```

No log: `Iniciando`, `Finalizando`, `Iniciando`, `Finalizando`. Nunca dois `Iniciando` seguidos. O tempo total fica no final. Deixa o número na tela — é a baseline que a próxima slide derruba.

## 4 — Threads

O mesmo trabalho, agora com várias threads. `ThreadPoolExecutor` com 10 workers, e o `map` entrega cada linha para `_lookup`. Cada worker pega uma ação: um CEP. Dez workers e vinte linhas são dez threads dentro de um processo. Quando uma termina, ela pega a próxima. O `map` devolve o resultado na ordem do CSV. O log segue a ordem em que a resposta chega.

**Ao vivo**

```powershell
python src/main.py threads --limit 20 --workers 10
```

Aqui aparecem vários `Iniciando` antes do primeiro `Finalizando`. `worker_0`, `worker_1`: cada um pegou uma linha. Compara o tempo total com o do slide anterior. A vitória. Comemora — mas não explica ainda. O próximo slide é o "por quê".

## 5 — Por que voou?

Aqui o GIL entra pela primeira vez — como segredo, não como vilão. O desenho da tela mostra o laço em cima, uma espera atrás da outra, e embaixo as quatro chamadas viajando juntas. O de baixo termina perto da chamada mais lenta do grupo, não da soma.

Por que voou? Imagina o GIL como um bastão no centro da sala: só quem está com o bastão roda Python. A thread A pega o bastão, manda o HTTPS, e como vai ficar parada esperando a rede, devolve o bastão — não precisa dele enquanto espera. A thread B pega o bastão e dispara a chamada dela. As duas estão esperando a internet ao mesmo tempo, mas o bastão só passa por uma mão de cada vez. A rede fica ocupada junta. O Python segue revezando um núcleo só.

A animação é o garçom único revezando as quatro mesas. Continua sendo um garçom: o Python reveza um núcleo, e quem anda junto é a rede. O nome disso é concorrência. O GIL continua ali — ele só não segura a thread durante a espera. Guarda esse "durante a espera". O próximo slide tira ele.

## 6 — A pegadinha

Faz a pergunta da tela antes de virar: e se não houver espera nenhuma? No ViaCEP a thread ganhava tempo porque ficava parada esperando a rede. Tira a rede. A ação trocou: em vez de buscar um CEP, cada thread carimba um bloco. A CPU trabalha o tempo inteiro, então a thread nunca devolve o bastão.

O trabalho é um carimbo de arquivo. O nome é SHA-256. Você entrega um conteúdo e recebe um código curto. O mesmo conteúdo, o mesmo código. Mudou um byte, o carimbo muda. Aqui a gente não confere arquivo de verdade — o `hash_blocks` carimba centenas de milhares de bloquinhos de 1024 bytes. O tamanho é de propósito: o `hashlib` só solta o GIL a partir de 2048 bytes. Abaixo disso, a trava fica presa na conta.

Deixa a pergunta no ar: as mesmas threads, o mesmo ThreadPool, vão voar de novo, certo? A resposta vem no próximo slide, e é não.

## 7 — Decepção + processos

A decepção primeiro. Nesse carimbo, com o GIL ligado, o `ThreadPoolExecutor` é o um garçom. Várias threads, um processo, um GIL. Elas se revezam no mesmo núcleo. O tempo empata com o sequencial. A thread nunca devolve o bastão — a CPU não para nunca, então não tem espera pra devolver. O vilão revelado: o mesmo segredo que salvou o ViaCEP agora trava o carimbo.

A solução. O `ProcessPoolExecutor` são os quatro garçons. Cada worker é outro processo, com seu Python e seu GIL. Quatro workers podem ocupar quatro núcleos ao mesmo tempo. Aí o ganho aparece. A animação da tela é o paralelismo: 4 garçons, 4 núcleos — só com processo. Um processo = outro Python, outro GIL, outro núcleo possível.

**Ao vivo, no Python com GIL**

```powershell
.\.venv\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4
```

A primeira linha diz que o GIL está ligado. A leitura no final: threads perto de 1x, processos na frente. A decepção e a solução, no mesmo comando.

## 8 — Sem o GIL

Gancho da tela: e se tirassem a trava? O slide anterior precisou de processo para ganhar núcleo, driblando o GIL por fora. E se a gente pudesse tirar o GIL por dentro? Desde o 3.13 existe um build oficial sem a trava: `python3.13t`, free-threaded, ainda experimental. É o mesmo `ThreadPoolExecutor` e o mesmo `hash_blocks`. Sem o GIL, aquelas threads deixam de ser o garçom único e passam a ocupar vários núcleos.

Bibliotecas em C podem quebrar nesse build. Essa demo usa só a biblioteca padrão. A checagem é `sys._is_gil_enabled()`, e aqui ela devolve `False`.

**Ao vivo, no free-threaded**

```powershell
.\.venv-ft\Scripts\python.exe src\main.py cpu --upto 800000 --workers 4
```

Mesmo comando do slide anterior. Desta vez as threads aceleram. A animação dos 4 garçons, que no slide 7 só acontecia com processo, agora acontece com thread também.

## 9 — Medido

Os dois slides anteriores, medidos. O mesmo carimbo, dois Pythons. Se o ao vivo ainda estiver rodando, esta tabela é uma medição já feita. O número mexe a cada execução. O padrão é o que importa.

Com o GIL ligado: sequencial 2,44s. Threads 2,60s, 0,94x — um núcleo só, e o overhead até deixa um pouco mais lento. Processos 1,32s, 1,85x.

Sem o GIL: o sequencial sobe para 3,17s. Esse build tem um custo. As threads caem para 1,11s, 2,87x. Processos 1,62s, 1,95x.

Com GIL, threads num núcleo só. Sem GIL, o ThreadPool ocupa vários núcleos. A tabela fecha o arco: o mesmo "às vezes" da capa, agora explicado.

## 10 — Três ideias

Fecha o caminho inteiro.

I/O-bound, a planilha: threads já ajudam hoje, porque a espera solta o GIL. É o um garçom, com a rede andando junta.

CPU-bound com GIL, o carimbo: o ThreadPool fica num núcleo só. Quem usa os outros núcleos é o processo, um garçom por núcleo.

Free-threaded: o mesmo ThreadPool finalmente ocupa vários núcleos.

Fecha com a regra de bolso da tela, que responde a pergunta mais comum — "então minhas threads rodam em núcleos diferentes?". Com o GIL, não: thread não espalha em núcleos, quem espalha é processo. Sem o GIL, sim, a thread também espalha. E cuidado com uma pegadinha: no I/O a thread acelera sem espalhar em núcleo nenhum — ali o ganho é a espera de rede se sobrepondo, não núcleo extra.

## 11 — Perguntas

O código está no repositório. A parte de CEP é o ViaCEP. A parte de CPU é o comando `cpu`. A comparação é a pasta `.venv` contra a `.venv-ft`.

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

O `cpu` não depende do ViaCEP. Segue do slide 6. A tabela do slide 9 fecha o argumento sem chamar a API.
