# Ametista

Conversor de imagens **portátil, offline e leve** para Windows.

- **V1**: fazia uma única coisa — **PNG → ICO**.
- **V1.2**: virou um conversor de imagens de verdade — **PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF e ICO, em qualquer combinação de entrada e saída**, mantendo tudo o que a V1 já fazia (perfis de tamanho para ICO, lote, pasta de saída, política de sobrescrita).

## Objetivo da V1.2
Selecionar uma ou várias imagens, escolher o formato de saída, ajustar só as opções que fazem sentido para aquele formato (perfil de tamanhos para ICO, qualidade para JPG/WEBP), converter e ver o resultado de cada arquivo (✓ convertido / ⚠ convertido com aviso / ✕ erro). Nenhum dado sai da máquina.

## Requisitos
- Python 3.10+ (só para desenvolvimento/build; o `.exe` final não exige Python)
- Windows (plataforma principal)

## Bibliotecas
- **Pillow** — leitura/gravação de todos os formatos suportados (obrigatória)
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
1. **Adicionar imagens** — clique na área tracejada ou arraste os arquivos até ela (PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF, ICO).
2. Em **Converter para**, escolha o formato de saída. As opções abaixo mudam de acordo:
   - **ICO** → perfil de tamanhos (Padrão, Ícone pequeno, Ícone grande ou Personalizado), igual à V1.
   - **JPG / JPEG / WEBP** → controle de qualidade (10–100%).
   - Demais formatos → sem opções extras.
3. Escolha a **pasta de saída** (padrão: a mesma pasta de cada arquivo) e, se quiser, marque **Abrir pasta após a conversão**.
4. Defina **Se já existir**: criar novo nome (padrão, `nome (1).ext`), sobrescrever ou pular.
5. Clique em **✦ CONVERTER IMAGENS** e acompanhe o resultado de cada arquivo na lista.

### Sobre casos especiais
- **Transparência → JPG/BMP/GIF**: como esses formatos não têm canal alfa, a imagem é composta sobre um fundo branco antes de salvar.
- **GIF animado**: apenas o primeiro quadro é convertido; o resultado aparece com ⚠ e uma mensagem explicando isso, em vez de gerar um arquivo incorreto silenciosamente.
- **ICO**: continua com fundo transparente, imagem centralizada em tela quadrada e múltiplas resoluções (16 a 256) no mesmo arquivo, não importa o formato de entrada.
- **Nome do arquivo**: mantém o nome original, trocando só a extensão.

## Estrutura
```
main.py                          ponto de entrada
app/core/base.py                 BaseConverter, Result, ConversionError
app/core/converter_manager.py    escolhe o conversor certo para cada par (entrada, saída)
app/core/settings.py             configurações (config/settings.json)
app/converters/formats.py        tabela única de formatos/extensões suportados
app/converters/imaging.py        abertura de imagem, GIF animado, achatamento de transparência
app/converters/ico_converter.py  conversor para .ico (qualquer formato de entrada)
app/converters/image_converter.py  conversor genérico entre os demais formatos de imagem
app/ui/                          janela principal, tema e widgets (zona de soltar, controle de qualidade)
app/utils/file_utils.py          caminhos e utilidades
app/utils/image_utils.py         miniaturas e detecção de formato/dimensões para a lista
assets/  config/                 recursos e configurações (relativos ao app)
```

## Como adicionar um novo conversor
1. Crie `app/converters/xxx.py` com uma classe que herda de `BaseConverter` e implementa:
   - `handles(source_ext, target_label)`: retorna `True` para os pares que ela resolve.
   - `convert(source, target, options)`: executa a conversão; pode devolver uma mensagem de aviso (`str`) ou `None`. Em caso de falha, levante `ConversionError("mensagem clara")`.
2. Registre em `ConverterManager.__init__`: `self.register(MeuConversor())`.
3. Se for um formato de imagem novo, acrescente-o em `app/converters/formats.py`; a interface (seletor de formato de saída, filtro de arquivos aceitos) já lê dessa tabela e não precisa ser alterada.
4. Para um grupo totalmente novo (documentos, áudio, vídeo), crie uma pasta própria em `app/converters/` e sua própria tabela de formatos — o `ConverterManager` não precisa saber a diferença.

## Versão
**Ametista v1.2** — conversor de imagens. Próximos passos possíveis: outros grupos de arquivo (documentos, áudio, vídeo), sempre como módulos novos, sem reescrever o núcleo.
