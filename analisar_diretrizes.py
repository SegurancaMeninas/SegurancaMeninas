import PyPDF2
from eca_digital_classifier import ECADigitalClassifier
import json
import os

def extrair_texto_pdf(caminho_pdf):
    texto = ""
    if not os.path.exists(caminho_pdf):
        raise FileNotFoundError(f"Arquivo {caminho_pdf} não encontrado.")
        
    with open(caminho_pdf, "rb") as f:
        leitor = PyPDF2.PdfReader(f)
        for pagina in leitor.pages:
            extraido = pagina.extract_text()
            if extraido:
                texto += extraido + "\n"
    return texto.strip()

# 1. Inicializa o classificador
classifier = ECADigitalClassifier("eca_digital_index.md", "eca_digital_schema.json")

conteudo_diretrizes = """
Página inicial da Central de Ajuda de Discord
Feedback
Enviar uma solicitação
Entrar
Artigos nessa seção
Verificação de idade para usuários brasileiros
Verificação de idade para usuários australianos
Perguntas frequentes de atualização de verificação de idade
Verificação de idade para usuários do Reino Unido
Como concluir a verificação de idade no Discord
Como consertar erros de telefone no Discord
Usando um aplicativo de autenticação no Discord
Chaves de segurança, passkeys e login sem senha no Discord
Como verificar sua conta do Discord
How to Remove a Phone Number From a Discord Account
Exibir mais
Discord  Configurações de conta  Segurança de conta
Pesquisa
Verificação de idade para usuários brasileiros

Buffy
há 2 meses Atualizado
Ainda não seguido por ninguém
Observação: no momento, estamos testando alguns métodos adicionais de verificação de idade, então você pode ver mais opções do que o listado abaixo.
A partir de 9 de março de 2026, estamos implementando a verificação de idade no Brasil para cumprir o Estatuto Digital para Crianças e Adolescentes (ECA Digital), que entra em vigor em 17 de março. Isso faz parte de uma regulamentação do governo que se aplica a uma ampla gama de serviços digitais que operam no Brasil.

Quando adiamos nosso lançamento global de verificação de idade em 24 de fevereiro, compartilhamos que ainda estamos comprometidos em atender aos requisitos legais nos países onde eles existem e o Brasil é um desses países. 

Essas mudanças trazem configurações de segurança padrão atualizadas, acesso limitado por idade a determinados conteúdos e espaços e uma verificação de idade avançada com privacidade, usando k-ID, para adultos que desejam acessar conteúdo com restrição de idade ou alterar certas configurações padrão. A maioria dos usuários que não acessa conteúdo com restrição de idade não precisará verificar de forma alguma.

Nosso objetivo continua o mesmo: aplicar as proteções certas para as faixas etárias certas, preservando a experiência de comunidade genuína que torna o Discord especial. Continuaremos atualizando a experiência do Discord no Brasil para se alinhar com a ECA Digital e lhe informaremos sobre essas mudanças conforme as fizermos.

O que esperar deste artigo:

O que está mudando para usuários brasileiros
Verificação de idade para privacidade
Configurações padrão de segurança
Configurações de conteúdo 
Configurações sociais
Perguntas frequentes
O que está mudando para usuários brasileiros
 
A partir de 17 de março de 2026, todos os usuários do Discord no Brasil terão mais configurações de proteção para apoiar adolescentes. Isso significa configurações de comunicação atualizadas, acesso restrito a espaços com restrição de idade e filtragem de conteúdo. Usuários brasileiros com 18 anos ou mais podem concluir uma verificação de idade para acessar conteúdo e espaços com restrição de idade ou ajustar configurações relevantes.

Verificação de idade para privacidade
A verificação de idade é a base desta nova experiência e foi projetada para respeitar suas escolhas e privacidade. Você pode escolher usar estimativa de idade facial ou enviar um documento de identificação, e planejamos introduzir mais opções no futuro. Esta experiência é fornecida pela k-ID, nosso fornecedor de verificação de idade.

Veja como construímos proteções de privacidade:

Processamento no dispositivo: selfies de vídeo para estimativa de idade facial nunca saem do seu dispositivo
Exclusão rápida: os documentos de identidade que vão diretamente para o k-ID nunca são vistos pelo Discord. Eles são excluídos imediatamente depois da confirmação da idade.
Verificação de idade direta: na maioria dos casos, você completa o processo uma vez e sua experiência do Discord se adapta à faixa etária verificada. Você pode ser solicitado a usar vários métodos apenas quando mais informações forem necessárias para atribuir uma faixa etária.
Status privado: seu status de verificação de idade está disponível apenas para você e não pode ser visto por outros, a menos que você escolha compartilhá-lo.
Após concluir a verificação, você receberá uma confirmação por mensagem direta da nossa conta oficial do Discord. Você pode visualizar sua faixa etária atribuída a qualquer momento em configurações de conta. Se você quiser recorrer ou tentar novamente o processo, você pode fazer isso lá também.

Observação: se você receber um e-mail ou mensagem de texto pedindo para verificar sua idade, não foi enviado por nós.  A verificação de idade só acontece dentro do Discord.
Se você ainda não confirmou sua idade, você precisará concluir uma verificação de idade ao tentar:

Remover o desfoque de conteúdo sensível em mídias sinalizado pelo nosso Filtro de conteúdo sensível ou tente mudar qualquer uma das configurações padrão do Filtro de conteúdo sensível para "Mostrar" conteúdo sensível.
Desativar as Solicitações de mensagens (elas estão ativadas por padrão para ajudá-lo a filtrar DMs indesejadas da sua lista de DM).
Acessar canais e servidores com restrição de idade (18+).
Falar em um Canal de palco.
Ativar a configuração de comandos restritos por idade.
Ativar a configuração “Permitir acesso a servidores NSFW no iOS”.
Para mais detalhes sobre como confirmar sua idade, consulte nosso artigo sobre Como concluir a verificação de idade no Discord.


Configurações padrão de segurança
Todos os usuários brasileiros novos e existentes terão configurações de segurança padrão. O Discord pode solicitar uma verificação de idade quando você tentar alterar determinadas configurações ou acessar conteúdo específico.

Configurações de conteúdo 
Filtros de conteúdo sensível estão ativados por padrão. As configurações padrão para esta funcionalidade deixarão borrados quaisquer conteúdos sinalizados em mensagens diretas e mensagens em canais do servidor, como também bloquearão quaisquer conteúdos sinalizados em mensagens diretas com estranhos. O que mudou é que a modificação dessas configurações de conteúdo padrão para "Mostrar" agora exigirá a verificação de idade.

 

Configurações de Filtro de conteúdo sensível
Remover o desfoque de conteúdo sinalizado por nossos filtros exigirá uma verificação de idade.
Tentar entrar em um canal restrito por idade (18+) e servidores restritos por idade exigirá uma verificação de idade.
Configurações sociais
As solicitações de mensagens estão ativadas por padrão e enviam todas as DMs de pessoas que não são amigos para um espaço separado para ajudar a revisar quaisquer mensagens recebidas. Desativar as solicitações de mensagens exigirá a verificação de idade.


Configurando solicitações de mensagens na página de Conteúdo e social
Você receberá um alerta antes de aceitar uma solicitação de amizade de um usuário desconhecido. Usuários desconhecidos são aqueles com quem você não tem amigos em comum ou servidores pequenos compartilhados (menos de 200 membros). Esses alertas podem ajudar a tomar decisões mais informadas sobre novas conexões. No momento, esses alertas não podem ser desativados.


Aceitar pedir de amizade? Alerta
Perguntas frequentes
P: Essas alterações se aplicam a todos os usuários do Discord no Brasil?

R: Sim, as funcionalidades e experiências descritas acima se aplicam a todas as contas brasileiras novas e existentes.

P: Quando preciso passar pela verificação de idade?

R: Você deve ser um adulto confirmado para acesso a conteúdo e espaços com restrição de idade ou para modificar certas configurações de segurança. A maioria dos usuários do Discord não acessa conteúdo com idade restrita e nunca precisará passar por um fluxo de estimativa de idade facial ou verificação de identidade. 

P: Você vai adicionar mais opções de métodos de verificação?

R: Estamos trabalhando ativamente para adicionar mais opções de verificação antes de expandir a verificação de idade globalmente. No entanto, alguns métodos podem não estar disponíveis em certas regiões que definiram padrões legais para quais métodos são aceitáveis.

P: Quais métodos de verificação de idade estão disponíveis?

R: Existem dois métodos principais disponíveis no momento:

Estimativa de idade facial (selfie de vídeo): usa a câmera do seu dispositivo para estimar ssua faixa etária. O processamento acontece inteiramente no seu dispositivo: sua selfie de vídeo nunca sai dele, e o Discord e nosso fornecedor, k-ID, nunca a recebem. Só recebemos sua faixa etária.
Escaneamento de ID: escaneie seu documento de identidade emitido pelo governo e tire uma selfie rápida para confirmar que ele corresponde. Seu ID e selfie são processados para confirmar sua idade e depois excluídos.
Observação: talvez seja necessário completar os dois métodos se não pudermos confirmar a faixa etária com confiança suficiente apenas na estimativa de idade facial.

Estamos trabalhando ativamente para adicionar mais opções de verificação antes de expandir a verificação de idade globalmente.

Para obter instruções passo a passo sobre cada método, consulte nosso artigo Como concluir a verificação de idade no Discord.

P: E se eu optar por não confirmar minha idade?

R: Se você optar por não realizar a verificação, eis exatamente o que acontece: você mantém sua conta, seus servidores, sua lista de amigos, suas mensagens diretas e bate-papo de voz. A única coisa que muda é que você não poderá acessar conteúdo com restrição de idade ou alterar certas configurações padrão feitas para proteger adolescentes. Nada mais sobre a sua experiência no Discord muda.

P: Como vocês escolhem os fornecedores com quem trabalham para verificação de idade?

R: Estamos trabalhando para documentar cada fornecedor de verificação e suas práticas em nosso site e deixaremos claro no produto quem é cada fornecedor. Também definimos um novo requisito: qualquer parceiro que ofereça a estimativa da idade facial deve realizá-la inteiramente no dispositivo. Se eles não atenderem a esse padrão, não trabalharemos com eles.

P: Como o Discord usa meus dados de verificação de idade?

R: Usamos essas informações para fins de segurança e para oferecer experiências adequadas à idade no Discord. Não usaremos as informações de verificação de idade para segmentar você com anúncios e não vendemos seus dados. Você pode controlar como usamos os seus dados.

P: Os meus dados pessoais são armazenados durante o processo de verificação de idade?

Resposta: Não. O Discord e seus parceiros confiáveis não armazenam permanentemente seus documentos pessoais de identidade ou selfies de vídeo. Documentos de identidade que vão diretamente para k-ID nunca são vistos pelo Discord. Eles são excluídos imediatamente depois da confirmação da idade. Selfies de vídeo para estimativa de idade facial são processadas inteiramente no dispositivo e nunca armazenadas. Sua identidade nunca está associada à sua conta Discord.

P: O que vocês estão recebendo do meu ID ou estimativa de idade facial? Quais informações pessoais vocês recebem?

R: O Discord só recebe a sua idade. Só isso. Sua identidade nunca está associada à sua conta.

P: E se a minha verificação de idade falhar ou mostrar resultados incorretos?

R: Se o processo de verificação de idade falhar ou exibir resultados incorretos, tente realizar a verificação novamente através das mensagens de sistema do Discord selecionando a opção "Tentar novamente". 

Se você foi incorretamente identificado como abaixo do requisito de idade mínima e deseja recorrer, siga as instruções aqui para usar a opção de escanear o documento para verificar sua data de nascimento.

Para obter mais informações sobre como lidar com problemas de verificação de idade, visite nosso artigo Como concluir a verificação de idade no Discord.
P: Preciso confirmar minha idade sempre que acessar conteúdo com restrição de idade ou tentar atualizar uma configuração padrão?

Resposta: Não. A verificação de idade é, normalmente, um processo único. Na maioria dos casos, os usuários completam o processo uma vez e sua experiência no Discord se adapta à faixa etária verificada. Os usuários podem ser solicitados a usar vários métodos apenas quando mais informações são necessárias para atribuir uma faixa etária.

P: O que acontece se minha idade for confirmada como menor de 18 anos?

R: Se sua idade for confirmada como inferior a 18 anos, certas configurações de segurança padrão permanecerão em vigor e não poderão ser alteradas. As definições incluem filtros de conteúdo sensível, configurações de solicitação de mensagens e restrições ao tentar acessar canais com restrição de idade.

P: O que acontece se minha idade for confirmada como muito jovem para estar no Discord?

R: Sua conta será suspensa se você estiver abaixo do requisito de idade mínima para estar no Discord. Se você acredita que sua idade verificada está incorreta, você pode tentar novamente o processo de verificação usando a opção de escaneamento de documento de identidade. 

Siga as instruções aqui para usar a opção de escanear o documento de identidade para verificar sua data de nascimento.

P: Posso recorrer se minha conta for classificada incorretamente como restrita por idade ou for banida?

R: Sim. Se você acredita que a verificação de sua faixa etária está incorreta e deseja recorrer, realize processo de verificação novamente usando a opção de escanear seu documento. 

Siga as instruções aqui para usar a opção de escanear o documento de identidade para verificar sua data de nascimento.

P: Como funcionam os filtros de segurança de conteúdo?

R: Os filtros de segurança de conteúdo do Discord são parte da nossa abordagem mais ampla de Assistência de Segurança para Adolescentes. Eles ajudam a reduzir a exposição a certas categorias de mídias potencialmente sensíveis baseadas em imagens, especialmente para adolescentes.

Filtro de mídia sexual para adultos: ajuda a identificar mídia visual que pode conter material sexualmente explícito ou sugestivo envolvendo adultos
Filtro de mídia gráfica: ajuda a identificar mídias baseadas em imagens que podem conter material visual violento ou potencialmente perturbador
Estes filtros se aplicam apenas a imagens e vídeos. Eles não verificam mensagens de texto, voz ou chamadas e são projetados para oferecer suporte a experiências adequadas à idade, preservando conversas privadas.

P: Existem planos para expandir essas mudanças para outras regiões?

R: Ainda estamos trabalhando na expansão das opções de verificação, publicando nossa metodologia para determinação automática da idade e garantindo que todos os fornecedores com os quais trabalhamos atendam nossos padrões de privacidade antes de lançarmos globalmente. Nosso lançamento global está planejado para o segundo semestre de 2026, enquanto construímos isso cuidadosamente. Enquanto isso, também podemos avançar em regiões, se a verificação de idade for exigida por regulamentação, em conformidade com as leis e requisitos regionais.


 

Share

  
Esse artigo foi útil?
 
Usuários que acharam isso útil: 122 de 273
Tem mais dúvidas? Envie uma solicitação
Artigos relacionados
Como concluir a verificação de idade no Discord
Como verificar sua conta do Discord
Verificação de idade para usuários australianos
Configurando a verificação em duas etapas
Perguntas frequentes de atualização de verificação de idade
Português do Brasil 
Mídias Sociais
Produto
Baixar
Nitro
Estado
Diretório de Apps
Empresa
Sobre
Empregos
Marca
Notícias
Recursos
Suporte
Segurança
Blog
Comentários
Criadores
Comunidade
Desenvolvedores
Missões
Lojinha oficial de terceiros
Política
Termos
Privacidade
Configurações de cookies
Diretrizes
Reconhecimentos
Licenças
Informações da empresa


DiscordAl hacer clic en “Aceptar todas las cookies”, usted acepta que las cookies se guarden en su dispositivo para mejorar la navegación del sitio, analizar el uso del mismo, y colaborar con nuestros estudios para marketing.
Configuración de cookies Rechazarlas todas Aceptar todas las cookies



"""

try:
    if len(conteudo_diretrizes.strip()) < 50:
        print("ERRO: O texto colado parece muito curto. Certifique-se de que colou o conteúdo corretamente.")
    else:
        print(f"Texto recebido ({len(conteudo_diretrizes)} caracteres).")
        print("Analisando conformidade com o ECA Digital via Groq...")
        
        resultado = classifier.classify(
            conteudo_diretrizes, 
            "Auditoria completa de conformidade com a Lei 15.211/2025"
        )

        print("\nAnálise Concluída!")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        with open("resultado_diretrizes.json", "w", encoding="utf-8") as f_out:
            json.dump(resultado, f_out, indent=2, ensure_ascii=False)

except Exception as e:
    print(f"Erro ao processar: {e}")