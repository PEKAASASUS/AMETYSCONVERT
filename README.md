# Ametista

Conversor de arquivos **portátil, offline e leve** para Windows. A V1 faz uma única coisa, bem feita: **PNG → ICO**.

## Objetivo da V1
Selecionar um ou vários PNGs, escolher a saída e o perfil de tamanhos, converter e ver o resultado de cada arquivo (✓ / ✕). Nenhum dado sai da máquina.

## Requisitos
- Python 3.10+ (só para desenvolvimento/build; o `.exe` final não exige Python)
- Windows (plataforma principal)

## Bibliotecas
- **Pillow** — leitura de PNG e gravação de ICO (obrigatória)
- **tkinterdnd2** — arrastar e soltar (opcional)
- **PyInstaller** — apenas para gerar o executável
- Interface: Tkinter (já incluso no Python)

## Executar em desenvolvimento
```
pip install -r requirements.txt
python main.py
```

## Gerar o executável portátil
```
build.bat
```
Resultado em `dist\Ametista\`. Copie a pasta inteira para o pendrive. `config\` (configurações e log) fica ao lado do `.exe`.

## Uso básico
1. **Adicionar PNGs** (ou arraste os arquivos).
2. Escolha a **pasta de saída** (padrão: a mesma de cada PNG).
3. Escolha o **perfil**: Padrão (16–256), Ícone pequeno, Ícone grande ou Personalizado.
4. Defina **Se já existir**: criar novo nome (padrão, `icone (1).ico`), sobrescrever ou pular.
5. **Converter** e confira a coluna de resultado.

PNGs não quadrados são centralizados em fundo transparente (sem distorção). A transparência é preservada.

## Estrutura
```
main.py                     ponto de entrada
app/core/base.py            BaseConverter, Result, ConversionError
app/core/converter_manager.py  registro e execução de conversores
app/core/settings.py        configurações (config/settings.json)
app/converters/png_to_ico.py   conversor PNG → ICO
app/ui/                     janela principal e tema
app/utils/file_utils.py     caminhos e utilidades
assets/  config/            recursos e configurações (relativos ao app)
```

## Como adicionar um novo conversor
1. Crie `app/converters/xxx_to_yyy.py` com uma classe que herda de `BaseConverter`, define `source_ext`, `target_ext` e implementa `convert(source, target, options)`. Em caso de falha, levante `ConversionError("mensagem clara")`.
2. Registre em `ConverterManager.__init__`: `self.register(MeuConversor())`.
3. Ajuste a interface (tipos de arquivo aceitos e opções) quando o segundo formato existir.
