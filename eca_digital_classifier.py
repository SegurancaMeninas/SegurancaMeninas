import json
import os
from groq import Groq

class ECADigitalClassifier:
    def __init__(self, index_path, schema_path):
        self.index = self._load_index(index_path)
        self.schema = self._load_schema(schema_path)

    def _load_index(self, index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_schema(self, schema_path):
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_prompt(self, case_context, analysis_focus=None):
        return f"""
Você atua como especialista em direito digital e proteção de crianças e adolescentes, com domínio aprofundado do ECA Digital e seus reflexos em plataformas digitais. Você tem acesso a um índice temático comprimido da Lei nº 15.211/2025 para guiar sua análise e referenciar dispositivos legais específicos de forma eficiente em termos de tokens.

### Objetivo central
Classificar o registro exclusivamente no formato JSON definido abaixo, utilizando o Foco da Análise (se fornecido) e o Índice Temático Comprimido para identificar os dispositivos legais mais relevantes. Você deve realizar uma análise de adequação completa, gerando um score de conformidade e listando o que já foi implementado e o que falta para a adequação total à Lei nº 15.211/2025.

### RESTRIÇÃO CRÍTICA DE CONTEXTO:
Analise EXCLUSIVAMENTE o texto fornecido abaixo no "Contexto do Caso". 

### REGRAS ABSOLUTAS:
1. IDENTIFIQUE o nome da plataforma no texto (ex: Discord). Use esse nome no campo "plataforma_digital_envolvida".
2. NÃO INVENTE dados. Se o texto não menciona algo, coloque como pendente ou nulo.

### Regras semânticas obrigatórias
1. **Campos `string`**: Uma única ideia jurídica, texto curto (3–10 palavras), vocabulário jurídico normalizado.
2. **Diferenciações obrigatórias**: Distinguir claramente o tipo de documento, âmbito de aplicação, natureza da violação/conformidade, princípios e deveres da plataforma.
3. **Análise de Adequação**: 
   - `score_conformidade`: Um valor de 0 a 100 baseado na proporção de itens implementados vs. exigidos pela lei no contexto analisado.
   - `itens_implementados`: Lista de funcionalidades ou políticas identificadas no texto que cumprem a lei.
   - `itens_pendentes`: Lista do que a lei exige mas não foi identificado ou está em desacordo no texto.
   - `gap_analise`: Descrição curta do que falta para a adequação completa.

### Conhecimento
*   **Índice Temático Comprimido da Lei nº 15.211/2025:**
{self.index}

### Padrão JSON de Resposta
```json
{json.dumps(self.schema, indent=2)}
```

### Documentação do Schema
*   **`analise_adequacao`**: Objeto contendo o diagnóstico de conformidade.
    - `score_conformidade`: Nota de 0 a 100.
    - `status_geral`: Ex: "Em conformidade parcial", "Não conforme", "Altamente conforme".
    - `itens_implementados`: Array de strings com o que já existe.
    - `itens_pendentes`: Array de strings com o que falta.
    - `gap_analise`: O que falta para a adequação completa.

---

Contexto do Caso: {case_context}
{f"Foco da Análise: {analysis_focus}" if analysis_focus else ""}

Retorne apenas o JSON puro.
"""

    def _call_llm(self, prompt):
        api_key = "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" 
        
        if not api_key or api_key == "SUA_CHAVE_AQUI":
            api_key = os.environ.get("GROQ_API_KEY")

        client = Groq(api_key=api_key)

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Você é um auditor jurídico rigoroso que analisa APENAS o texto fornecido, sem usar conhecimento externo."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return completion.choices[0].message.content

    def classify(self, case_context, analysis_focus=None):
        prompt = self._build_prompt(case_context, analysis_focus)
        res_str = self._call_llm(prompt)
        try:
            return json.loads(res_str)
        except:
            clean_res = res_str.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_res)

if __name__ == "__main__":
    try:
        classifier = ECADigitalClassifier("eca_digital_index.md", "eca_digital_schema.json")
        print("Motor pronto para análise de conformidade.")
    except Exception as e:
        print(f"Erro: {e}")
