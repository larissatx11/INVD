### Transformação dos Dados – CSV Tratado

Após a ingestão dos dados de sensores via CSV, realizamos uma **transformação no CSV bruto** que adiciona colunas derivadas com **informações enriquecidas** para análise no Data Lake.

#### Dados Originais

Informações do arquivo `saida_csv.csv`:

| Campo         | Descrição                                                                 |
|---------------|---------------------------------------------------------------------------|
| `id`          | Identificador único do registro                                           |
| `createdAt`   | Data de criação do registro                                               |
| `updatedAt`   | Data de atualização                                                       |
| `fullWeight`  | Peso total da colmeia (estrutura + mel + abelhas)                        |
| `honeyWeight` | Peso do mel na colmeia                                                    |
| `pressure`    | Pressão atmosférica local                                                 |

---

#### Campos adicionados na transformação

- **`variacao_peso`**: diferença entre o `fullWeight` atual e o anterior.  
  - Serve como indicativo de entrada/saída de néctar, evasão de abelhas ou necessidade de intervenção.

- **`necessidade_alimentacao`**: valor booleano (`True` ou `False`) indicando se o `honeyWeight` permaneceu zerado em ao menos 3 registros consecutivos.  
  - Pode sugerir que a colmeia está sem produção de mel, sendo necessário alimentar artificialmente.

- **`pressao_anomala`**: `True` se a pressão atmosférica estiver fora do intervalo saudável (980 a 1030 hPa).  
  - Pressões muito baixas ou muito altas podem antecipar mudanças climáticas bruscas que impactam a atividade das abelhas.

---

#### Colunas Derivadas no `saida_csv_tratado.csv`

| Novo Campo               | Lógica                                                | Descrição                                                         |
|--------------------------|-------------------------------------------------------|-------------------------------------------------------------------|
| `variacao_peso`          | Diferença de `fullWeight` em relação ao anterior     | Ajuda a monitorar ganho/perda de peso da colmeia                 |
| `necessidade_alimentacao`| `True` se os **últimos 3 registros** de `honeyWeight` forem 0 | Indica possível falta de alimento (sem produção de mel)     |
| `pressao_anomala`        | `True` se `pressure` estiver **fora de 980–1030**     | Detecta condição atmosférica incomum                              |

---

#### Finalidade

Essas transformações permitem:

- Análises mais inteligentes sobre saúde e produtividade das colmeias
- Geração de alertas automáticos com base em padrões
- Visualização direta em dashboards sem precisar tratar os dados manualmente
