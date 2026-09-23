---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- generated_from_trainer
- dataset_size:87142
- loss:MultipleNegativesRankingLoss
base_model: BAAI/bge-base-en-v1.5
widget:
- source_sentence: A flaw was found in dmg2img through 20170502. fill_mishblk() does
    not check the length of the read buffer, and copy 0xCC bytes from it. The length
    of the buffer is controlled by an attacker. By providing a length smaller than
    0xCC, memcpy reaches out of the malloc'ed bound. This possibly leads to memory
    layout information leaking in the data. This might be used in a chain of vulnerability
    in order to reach code execution.
  sentences:
  - 'SI-16: Memory Protection. Implement the following controls to protect the system
    memory from unauthorized code execution: {{ insert: param, si-16_odp }}.'
  - 'SI-10: Information Input Validation. Check the validity of the following information
    inputs: {{ insert: param, si-10_odp }}.'
  - 'SI-16: Memory Protection. Implement the following controls to protect the system
    memory from unauthorized code execution: {{ insert: param, si-16_odp }}.'
- source_sentence: 'Improper Input Validation vulnerability in CyberArk CyberArk Secure
    Web Sessions Extension on Chrome, Edge allows Denial of Service when trying to
    starting new SWS sessions.This issue affects CyberArk Secure Web Sessions Extension:
    before 2.2.30305.'
  sentences:
  - 'SI-10: Information Input Validation. Check the validity of the following information
    inputs: {{ insert: param, si-10_odp }}.'
  - 'AC-17: Remote Access. Establish and document usage restrictions, configuration/connection
    requirements, and implementation guidance for each type of remote access allowed;
    and

    Authorize each type of remote access to the system prior to allowing such connections.'
  - 'SI-10: Information Input Validation. Check the validity of the following information
    inputs: {{ insert: param, si-10_odp }}.'
- source_sentence: 'Cross-Site Request Forgery (CSRF) vulnerability in CleverReach®
    Official CleverReach Plugin for WooCommerce cleverreach-wc allows Cross Site Request
    Forgery.This issue affects Official CleverReach Plugin for WooCommerce: from n/a
    through <= 3.4.6.'
  sentences:
  - 'SI-2: Flaw Remediation. Identify, report, and correct system flaws;

    Test software and firmware updates related to flaw remediation for effectiveness
    and potential side effects before installation;

    Install security-relevant software and firmware updates within {{ insert: param,
    si-02_odp }} of the release of the updates; and

    Incorporate flaw remediation into the organizational configuration management
    process.'
  - 'SI-10: Information Input Validation. Check the validity of the following information
    inputs: {{ insert: param, si-10_odp }}.'
  - 'SI-10: Information Input Validation. Check the validity of the following information
    inputs: {{ insert: param, si-10_odp }}.'
- source_sentence: WBCE CMS 1.6.1 contains a stored cross-site scripting vulnerability
    that allows authenticated attackers to inject malicious JavaScript by uploading
    crafted SVG files through the media manager. Attackers can upload SVG files containing
    script tags to the /wbce/modules/elfinder/ef/php/connector.wbce.php endpoint and
    execute JavaScript when victims access the uploaded file.
  sentences:
  - 'SI-10: Information Input Validation. Check the validity of the following information
    inputs: {{ insert: param, si-10_odp }}.'
  - 'SI-10: Information Input Validation. Check the validity of the following information
    inputs: {{ insert: param, si-10_odp }}.'
  - 'SI-10: Information Input Validation. Check the validity of the following information
    inputs: {{ insert: param, si-10_odp }}.'
- source_sentence: 'Foxit PDF Reader PRC File Parsing Out-Of-Bounds Read Information
    Disclosure Vulnerability. This vulnerability allows remote attackers to disclose
    sensitive information on affected installations of Foxit PDF Reader. User interaction
    is required to exploit this vulnerability in that the target must visit a malicious
    page or open a malicious file.


    The specific flaw exists within the parsing of PRC files. The issue results from
    the lack of proper validation of user-supplied data, which can result in a read
    past the end of an allocated object. An attacker can leverage this in conjunction
    with other vulnerabilities to execute arbitrary code in the context of the current
    process. Was ZDI-CAN-26802.'
  sentences:
  - 'SI-16: Memory Protection. Implement the following controls to protect the system
    memory from unauthorized code execution: {{ insert: param, si-16_odp }}.'
  - 'SI-10: Information Input Validation. Check the validity of the following information
    inputs: {{ insert: param, si-10_odp }}.'
  - 'SI-16: Memory Protection. Implement the following controls to protect the system
    memory from unauthorized code execution: {{ insert: param, si-16_odp }}.'
pipeline_tag: sentence-similarity
library_name: sentence-transformers
metrics:
- cosine_accuracy@1
- cosine_accuracy@3
- cosine_accuracy@5
- cosine_accuracy@10
- cosine_precision@1
- cosine_precision@3
- cosine_precision@5
- cosine_precision@10
- cosine_recall@1
- cosine_recall@3
- cosine_recall@5
- cosine_recall@10
- cosine_ndcg@10
- cosine_mrr@10
- cosine_map@100
model-index:
- name: SentenceTransformer based on BAAI/bge-base-en-v1.5
  results:
  - task:
      type: information-retrieval
      name: Information Retrieval
    dataset:
      name: nist validation
      type: nist_validation
    metrics:
    - type: cosine_accuracy@1
      value: 0.8
      name: Cosine Accuracy@1
    - type: cosine_accuracy@3
      value: 0.8425
      name: Cosine Accuracy@3
    - type: cosine_accuracy@5
      value: 0.862
      name: Cosine Accuracy@5
    - type: cosine_accuracy@10
      value: 0.88
      name: Cosine Accuracy@10
    - type: cosine_precision@1
      value: 0.8
      name: Cosine Precision@1
    - type: cosine_precision@3
      value: 0.2808333333333333
      name: Cosine Precision@3
    - type: cosine_precision@5
      value: 0.17240000000000003
      name: Cosine Precision@5
    - type: cosine_precision@10
      value: 0.088
      name: Cosine Precision@10
    - type: cosine_recall@1
      value: 0.8
      name: Cosine Recall@1
    - type: cosine_recall@3
      value: 0.8425
      name: Cosine Recall@3
    - type: cosine_recall@5
      value: 0.862
      name: Cosine Recall@5
    - type: cosine_recall@10
      value: 0.88
      name: Cosine Recall@10
    - type: cosine_ndcg@10
      value: 0.8386651897874349
      name: Cosine Ndcg@10
    - type: cosine_mrr@10
      value: 0.8255313492063487
      name: Cosine Mrr@10
    - type: cosine_map@100
      value: 0.8277401287969374
      name: Cosine Map@100
---

# SentenceTransformer based on BAAI/bge-base-en-v1.5

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [BAAI/bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5). It maps sentences & paragraphs to a 768-dimensional dense vector space and can be used for retrieval.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [BAAI/bge-base-en-v1.5](https://huggingface.co/BAAI/bge-base-en-v1.5) <!-- at revision a5beb1e3e68b9ab74eb54cfd186867f64f240e1a -->
- **Maximum Sequence Length:** 512 tokens
- **Output Dimensionality:** 768 dimensions
- **Similarity Function:** Cosine Similarity
- **Supported Modality:** Text
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/huggingface/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'transformer_task': 'feature-extraction', 'modality_config': {'text': {'method': 'forward', 'method_output_name': 'last_hidden_state'}}, 'module_output_name': 'token_embeddings', 'architecture': 'BertModel'})
  (1): Pooling({'embedding_dimension': 768, 'pooling_mode': 'cls', 'include_prompt': True})
  (2): Normalize({})
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```
Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
queries = [
    'Foxit PDF Reader PRC File Parsing Out-Of-Bounds Read Information Disclosure Vulnerability. This vulnerability allows remote attackers to disclose sensitive information on affected installations of Foxit PDF Reader. User interaction is required to exploit this vulnerability in that the target must visit a malicious page or open a malicious file.\n\nThe specific flaw exists within the parsing of PRC files. The issue results from the lack of proper validation of user-supplied data, which can result in a read past the end of an allocated object. An attacker can leverage this in conjunction with other vulnerabilities to execute arbitrary code in the context of the current process. Was ZDI-CAN-26802.',
]
documents = [
    'SI-16: Memory Protection. Implement the following controls to protect the system memory from unauthorized code execution: {{ insert: param, si-16_odp }}.',
    'SI-16: Memory Protection. Implement the following controls to protect the system memory from unauthorized code execution: {{ insert: param, si-16_odp }}.',
    'SI-10: Information Input Validation. Check the validity of the following information inputs: {{ insert: param, si-10_odp }}.',
]
query_embeddings = model.encode_query(queries)
document_embeddings = model.encode_document(documents)
print(query_embeddings.shape, document_embeddings.shape)
# [1, 768] [3, 768]

# Get the similarity scores for the embeddings
similarities = model.similarity(query_embeddings, document_embeddings)
print(similarities)
# tensor([[0.9776, 0.9776, 0.5198]])
```
<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

## Evaluation

### Metrics

#### Information Retrieval

* Dataset: `nist_validation`
* Evaluated with [<code>InformationRetrievalEvaluator</code>](https://sbert.net/docs/package_reference/sentence_transformer/evaluation.html#sentence_transformers.sentence_transformer.evaluation.InformationRetrievalEvaluator)

| Metric              | Value      |
|:--------------------|:-----------|
| cosine_accuracy@1   | 0.8        |
| cosine_accuracy@3   | 0.8425     |
| cosine_accuracy@5   | 0.862      |
| cosine_accuracy@10  | 0.88       |
| cosine_precision@1  | 0.8        |
| cosine_precision@3  | 0.2808     |
| cosine_precision@5  | 0.1724     |
| cosine_precision@10 | 0.088      |
| cosine_recall@1     | 0.8        |
| cosine_recall@3     | 0.8425     |
| cosine_recall@5     | 0.862      |
| cosine_recall@10    | 0.88       |
| **cosine_ndcg@10**  | **0.8387** |
| cosine_mrr@10       | 0.8255     |
| cosine_map@100      | 0.8277     |

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 87,142 training samples
* Columns: <code>sentence_0</code> and <code>sentence_1</code>
* Approximate statistics based on the first 100 samples:
  |          | sentence_0                                                                          | sentence_1                                                                         |
  |:---------|:------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------|
  | type     | string                                                                              | string                                                                             |
  | modality | text                                                                                | text                                                                               |
  | details  | <ul><li>min: 10 tokens</li><li>mean: 83.18 tokens</li><li>max: 439 tokens</li></ul> | <ul><li>min: 29 tokens</li><li>mean: 39.68 tokens</li><li>max: 95 tokens</li></ul> |
* Samples:
  | sentence_0                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | sentence_1                                                                                                                                |
  |:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------|
  | <code>This vulnerability allows remote attackers to execute arbitrary code on affected installations of DevExpress. Authentication is required to exploit this vulnerability. The specific flaw exists within the SafeBinaryFormatter library. The issue results from the lack of proper validation of user-supplied data, which can result in deserialization of untrusted data. An attacker can leverage this vulnerability to execute code in the context of the service account. Was ZDI-CAN-16710.</code> | <code>SI-10: Information Input Validation. Check the validity of the following information inputs: {{ insert: param, si-10_odp }}.</code> |
  | <code>The Table Field Add-on for ACF and SCF plugin for WordPress is vulnerable to Stored Cross-Site Scripting via the Table Cell Content in all versions up to, and including, 1.3.30 due to insufficient input sanitization and output escaping. This makes it possible for authenticated attackers, with Author-level access and above, to inject arbitrary web scripts in pages that will execute whenever a user accesses an injected page.</code>                                                        | <code>SI-10: Information Input Validation. Check the validity of the following information inputs: {{ insert: param, si-10_odp }}.</code> |
  | <code>Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') vulnerability in VillaTheme Abandoned Cart Recovery for WooCommerce woo-abandoned-cart-recovery allows Stored XSS.This issue affects Abandoned Cart Recovery for WooCommerce: from n/a through <= 1.1.10.</code>                                                                                                                                                                                                    | <code>SI-10: Information Input Validation. Check the validity of the following information inputs: {{ insert: param, si-10_odp }}.</code> |
* Loss: [<code>MultipleNegativesRankingLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#multiplenegativesrankingloss) with these parameters:
  ```json
  {
      "scale": 20.0,
      "similarity_fct": "cos_sim",
      "gather_across_devices": false,
      "directions": [
          "query_to_doc"
      ],
      "partition_mode": "joint",
      "hardness_mode": null,
      "hardness_strength": 0.0
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `per_device_train_batch_size`: 8
- `num_train_epochs`: 3
- `max_steps`: -1
- `learning_rate`: 5e-05
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: None
- `warmup_steps`: 0
- `optim`: adamw_torch
- `optim_args`: None
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `optim_target_modules`: None
- `gradient_accumulation_steps`: 1
- `average_tokens_across_devices`: True
- `max_grad_norm`: 1
- `label_smoothing_factor`: 0.0
- `bf16`: False
- `fp16`: False
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `use_cache`: False
- `neftune_noise_alpha`: None
- `torch_empty_cache_steps`: None
- `auto_find_batch_size`: False
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `include_num_input_tokens_seen`: no
- `log_level`: passive
- `log_level_replica`: warning
- `disable_tqdm`: False
- `project`: huggingface
- `trackio_space_id`: None
- `trackio_bucket_id`: None
- `trackio_static_space_id`: None
- `per_device_eval_batch_size`: 8
- `prediction_loss_only`: True
- `eval_on_start`: False
- `eval_do_concat_batches`: True
- `eval_use_gather_object`: False
- `eval_accumulation_steps`: None
- `include_for_metrics`: []
- `batch_eval_metrics`: False
- `save_only_model`: False
- `save_on_each_node`: False
- `enable_jit_checkpoint`: False
- `push_to_hub`: False
- `hub_private_repo`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_always_push`: False
- `hub_revision`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `restore_callback_states_from_checkpoint`: False
- `full_determinism`: False
- `seed`: 42
- `data_seed`: None
- `use_cpu`: False
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `parallelism_config`: None
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `dataloader_prefetch_factor`: None
- `remove_unused_columns`: True
- `label_names`: None
- `train_sampling_strategy`: random
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `ddp_static_graph`: None
- `ddp_backend`: None
- `ddp_timeout`: 1800
- `fsdp`: None
- `fsdp_config`: None
- `deepspeed`: None
- `debug`: []
- `skip_memory_metrics`: True
- `do_predict`: False
- `resume_from_checkpoint`: None
- `warmup_ratio`: None
- `local_rank`: -1
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Training Logs
| Epoch  | Step  | Training Loss | nist_validation_cosine_ndcg@10 |
|:------:|:-----:|:-------------:|:------------------------------:|
| 0.0459 | 500   | 1.3486        | 0.6090                         |
| 0.0918 | 1000  | 1.2181        | 0.7652                         |
| 0.1377 | 1500  | 1.2065        | 0.7556                         |
| 0.1836 | 2000  | 1.2245        | 0.7302                         |
| 0.2295 | 2500  | 1.2225        | 0.7529                         |
| 0.2754 | 3000  | 1.2189        | 0.7366                         |
| 0.3213 | 3500  | 1.2033        | 0.7520                         |
| 0.3672 | 4000  | 1.2093        | 0.7893                         |
| 0.4131 | 4500  | 1.2406        | 0.7948                         |
| 0.4590 | 5000  | 1.1858        | 0.7618                         |
| 0.5049 | 5500  | 1.1902        | 0.8109                         |
| 0.5508 | 6000  | 1.2181        | 0.8082                         |
| 0.5967 | 6500  | 1.2029        | 0.7343                         |
| 0.6426 | 7000  | 1.1972        | 0.8013                         |
| 0.6885 | 7500  | 1.1824        | 0.7839                         |
| 0.7344 | 8000  | 1.2011        | 0.7746                         |
| 0.7803 | 8500  | 1.1927        | 0.7885                         |
| 0.8262 | 9000  | 1.2108        | 0.7679                         |
| 0.8721 | 9500  | 1.1729        | 0.7636                         |
| 0.9180 | 10000 | 1.1948        | 0.7350                         |
| 0.9639 | 10500 | 1.1706        | 0.7250                         |
| 1.0    | 10893 | -             | 0.8052                         |
| 1.0098 | 11000 | 1.1825        | 0.8112                         |
| 1.0557 | 11500 | 1.1593        | 0.7957                         |
| 1.1016 | 12000 | 1.1813        | 0.8344                         |
| 1.1475 | 12500 | 1.1259        | 0.8148                         |
| 1.1934 | 13000 | 1.1946        | 0.7986                         |
| 1.2393 | 13500 | 1.1911        | 0.8207                         |
| 1.2852 | 14000 | 1.1545        | 0.8387                         |


### Training Time
- **Training**: 44.9 minutes
- **Evaluation**: 3.9 minutes
- **Total**: 48.8 minutes

### Framework Versions
- Python: 3.12.10
- Sentence Transformers: 5.6.0
- Transformers: 5.13.0
- PyTorch: 2.5.1+cu121
- Accelerate: 1.14.0
- Datasets: 5.0.0
- Tokenizers: 0.22.2

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

#### MultipleNegativesRankingLoss
```bibtex
@misc{oord2019representationlearningcontrastivepredictive,
      title={Representation Learning with Contrastive Predictive Coding},
      author={Aaron van den Oord and Yazhe Li and Oriol Vinyals},
      year={2019},
      eprint={1807.03748},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/1807.03748},
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->