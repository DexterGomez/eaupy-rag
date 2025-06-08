from unstructured_ingest.v2.pipeline.pipeline import Pipeline
from unstructured_ingest.v2.interfaces import ProcessorConfig
from unstructured_ingest.v2.processes.partitioner import PartitionerConfig
from unstructured_ingest.v2.processes.chunker import ChunkerConfig


import os

from unstructured_ingest.v2.processes.connectors.local import (
    LocalIndexerConfig,
    LocalDownloaderConfig,
    LocalConnectionConfig,
    LocalUploaderConfig
)


if __name__ == "__main__":
    
    Pipeline.from_configs(
        context=ProcessorConfig(),

        indexer_config=LocalIndexerConfig(input_path="data/raw/Effective_Altruism_Handbook.pdf"),

        downloader_config=LocalDownloaderConfig(),

        source_connection_config=LocalConnectionConfig(),

        partitioner_config=PartitionerConfig(
            api_key=os.getenv("UNSTRUCTURED_API_KEY"),
            strategy="auto"
        ),
        
        uploader_config=LocalUploaderConfig(output_dir="./data/processed/"),
        chunker_config=ChunkerConfig(chunking_strategy="by_tittle")
    ).run()