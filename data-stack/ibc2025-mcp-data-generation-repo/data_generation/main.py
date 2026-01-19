import os
import sys
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
import click
from tqdm import tqdm
import json

from generators.customer_generator import CustomerGenerator
from generators.title_generator import TitleGenerator
from generators.telemetry_generator import TelemetryGenerator
from generators.campaign_generator import CampaignGenerator

class DataGenerator:
    def __init__(self, output_dir: str = 'output', seed: int = 42):
        self.output_dir = output_dir
        self.seed = seed
        self._create_output_directories()
        
    def _create_output_directories(self):
        directories = [
            os.path.join(self.output_dir, 'customers'),
            os.path.join(self.output_dir, 'titles'),
            os.path.join(self.output_dir, 'telemetry'),
            os.path.join(self.output_dir, 'campaigns')
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def generate_all_data(self, num_customers: int = 100000, 
                         num_titles: int = 10000,
                         num_telemetry_events: int = 10000000,
                         num_campaigns: int = 500):
        
        click.echo(f"Starting data generation with seed: {self.seed}")
        
        # Generate customers
        click.echo("\n1. Generating customer data...")
        customer_gen = CustomerGenerator(seed=self.seed)
        customers_df = customer_gen.generate_customers(num_customers)
        self._save_to_parquet(customers_df, 'customers/customers.parquet')
        click.echo(f"   Generated {len(customers_df):,} customers")
        
        # Generate titles
        click.echo("\n2. Generating title data...")
        title_gen = TitleGenerator(seed=self.seed)
        titles_df = title_gen.generate_titles(num_titles)
        self._save_to_parquet(titles_df, 'titles/titles.parquet')
        click.echo(f"   Generated {len(titles_df):,} titles")
        
        # Generate telemetry events
        click.echo("\n3. Generating telemetry data...")
        telemetry_gen = TelemetryGenerator(customers_df, titles_df, seed=self.seed)
        
        # Generate in batches for memory efficiency
        batch_size = 1000000
        num_batches = (num_telemetry_events + batch_size - 1) // batch_size
        
        for i in tqdm(range(num_batches), desc="   Generating telemetry batches"):
            events_in_batch = min(batch_size, num_telemetry_events - i * batch_size)
            telemetry_df = telemetry_gen.generate_telemetry_events(events_in_batch)
            
            # Partition by date for better query performance
            telemetry_df['date'] = telemetry_df['event_timestamp'].dt.date
            
            # Save each batch with partitioning
            for date, date_df in telemetry_df.groupby('date'):
                date_str = date.strftime('%Y%m%d')
                filename = f'telemetry/date={date_str}/batch_{i:04d}.parquet'
                os.makedirs(os.path.dirname(os.path.join(self.output_dir, filename)), exist_ok=True)
                self._save_to_parquet(date_df.drop('date', axis=1), filename)
        
        click.echo(f"   Generated {num_telemetry_events:,} telemetry events")
        
        # Generate ad campaigns
        click.echo("\n4. Generating ad campaign data...")
        campaign_gen = CampaignGenerator(seed=self.seed)
        campaigns_df = campaign_gen.generate_campaigns(num_campaigns)
        self._save_to_parquet(campaigns_df, 'campaigns/campaigns.parquet')
        click.echo(f"   Generated {len(campaigns_df):,} ad campaigns")
        
        # Generate metadata
        self._generate_metadata({
            'generation_timestamp': datetime.now().isoformat(),
            'seed': self.seed,
            'num_customers': num_customers,
            'num_titles': num_titles,
            'num_telemetry_events': num_telemetry_events,
            'num_campaigns': num_campaigns
        })
        
        click.echo("\nData generation complete!")
        click.echo(f"Output directory: {os.path.abspath(self.output_dir)}")
    
    def _save_to_parquet(self, df: pd.DataFrame, filename: str):
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert list columns to JSON strings for Parquet compatibility
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    if isinstance(df[col].iloc[0], list):
                        df[col] = df[col].apply(json.dumps)
                except:
                    pass
        
        # Write to Parquet with compression
        df.to_parquet(filepath, engine='pyarrow', compression='snappy', index=False)
    
    def _generate_metadata(self, metadata: dict):
        metadata_path = os.path.join(self.output_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

@click.command()
@click.option('--customers', default=100000, help='Number of customers to generate')
@click.option('--titles', default=10000, help='Number of titles to generate')
@click.option('--telemetry', default=10000000, help='Number of telemetry events to generate')
@click.option('--campaigns', default=500, help='Number of ad campaigns to generate')
@click.option('--output-dir', default='output', help='Output directory for generated data')
@click.option('--seed', default=42, help='Random seed for reproducibility')
def main(customers, titles, telemetry, campaigns, output_dir, seed):
    """Generate synthetic data for Acme Corp video streaming platform."""
    
    generator = DataGenerator(output_dir=output_dir, seed=seed)
    generator.generate_all_data(
        num_customers=customers,
        num_titles=titles,
        num_telemetry_events=telemetry,
        num_campaigns=campaigns
    )

if __name__ == '__main__':
    main()