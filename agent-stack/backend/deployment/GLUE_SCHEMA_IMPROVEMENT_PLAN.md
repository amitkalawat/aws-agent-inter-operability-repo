# AWS Glue Schema Improvement Plan for ACME Telemetry Tables

## Executive Summary
The current ACME telemetry tables use VARCHAR data type for timestamp fields, causing query complexity and performance issues. This document outlines a comprehensive plan to migrate to proper TIMESTAMP data types and optimize the schema for better performance.

## Current Issues

### 1. Data Type Problems
- **event_timestamp** stored as VARCHAR instead of TIMESTAMP
- Requires `CAST(event_timestamp AS timestamp)` or `try_cast()` in every query
- Error-prone: "INVALID_CAST_ARGUMENT" errors when format varies
- Performance overhead from runtime type conversion

### 2. Query Complexity
```sql
-- Current (complex and error-prone)
WHERE CAST(t.event_timestamp AS timestamp) >= current_timestamp - INTERVAL '2' HOUR

-- Desired (simple and efficient)
WHERE t.event_timestamp >= current_timestamp - INTERVAL '2' HOUR
```

### 3. Affected Tables
- `acme_telemetry.telemetry` (real-time data)
- `acme_telemetry.video_telemetry_json` (JSON-formatted real-time)
- `acme_streaming_data.telemetry` (historical data)
- `acme_streaming_data.campaigns` (potentially other timestamp fields)
- `acme_streaming_data.customers` (subscription dates, created_at, updated_at)
- `acme_streaming_data.titles` (release_date, created_at, updated_at)

## Proposed Solution

### Phase 1: Discovery & Analysis (Day 1)

#### 1.1 Schema Investigation
```sql
-- Get current schema definition
DESCRIBE acme_telemetry.telemetry;
DESCRIBE acme_streaming_data.telemetry;

-- Sample timestamp formats
SELECT 
    event_timestamp,
    LENGTH(event_timestamp) as ts_length,
    COUNT(*) as count
FROM acme_telemetry.telemetry
GROUP BY event_timestamp, LENGTH(event_timestamp)
LIMIT 10;
```

#### 1.2 Data Format Analysis
- Document all timestamp format variations (e.g., "2025-08-13T06:08:46.600648Z")
- Identify any inconsistent formats
- Check for NULL values or empty strings
- Validate timezone information

#### 1.3 Impact Assessment
- List all queries/applications using these tables
- Identify downstream dependencies
- Calculate data volume for migration planning
- Estimate query performance improvements

### Phase 2: Schema Design (Day 2)

#### 2.1 New Table Schema
```sql
-- Proposed optimized schema
CREATE EXTERNAL TABLE acme_telemetry.telemetry_v2 (
    event_id string,
    customer_id string,
    title_id string,
    session_id string,
    event_type string,
    event_timestamp timestamp,  -- Changed from VARCHAR
    watch_duration_seconds int,
    position_seconds int,
    completion_percentage decimal(5,2),
    device_type string,
    device_id string,
    device_os string,
    app_version string,
    quality string,
    bandwidth_mbps decimal(10,2),
    buffering_events int,
    buffering_duration_seconds int,
    error_count int,
    ip_address string,
    country string,
    state string,
    city string,
    isp string,
    connection_type string
)
PARTITIONED BY (
    year int,
    month int,
    day int
)
STORED AS PARQUET
LOCATION 's3://acme-athena-results-241533163649/telemetry_v2/'
TBLPROPERTIES (
    'compression'='SNAPPY',
    'projection.enabled'='true',
    'projection.year.type'='integer',
    'projection.year.range'='2024,2030',
    'projection.month.type'='integer',
    'projection.month.range'='1,12',
    'projection.day.type'='integer',
    'projection.day.range'='1,31'
);
```

#### 2.2 Data Type Standardization
| Column | Current Type | Proposed Type | Benefit |
|--------|-------------|---------------|---------|
| event_timestamp | VARCHAR | TIMESTAMP | Native date operations |
| created_at | VARCHAR | TIMESTAMP | Consistent timestamps |
| updated_at | VARCHAR | TIMESTAMP | Consistent timestamps |
| subscription_start_date | VARCHAR | DATE | Proper date type |
| subscription_end_date | VARCHAR | DATE | Proper date type |
| release_date | VARCHAR | DATE | Proper date type |

#### 2.3 Additional Optimizations
- **Partitioning**: By date (year/month/day) for time-series queries
- **File Format**: Convert to Parquet for better compression and performance
- **Compression**: Use SNAPPY for balance of speed and size
- **Statistics**: Enable automatic statistics collection

### Phase 3: Migration Strategy (Days 3-4)

#### 3.1 Backward Compatibility Views
```sql
-- Create views for backward compatibility during transition
CREATE OR REPLACE VIEW acme_telemetry.telemetry_compat AS
SELECT 
    event_id,
    customer_id,
    title_id,
    session_id,
    event_type,
    CAST(event_timestamp AS VARCHAR) as event_timestamp,  -- Cast back for compatibility
    -- ... other columns
FROM acme_telemetry.telemetry_v2;
```

#### 3.2 Data Migration Script
```python
# Pseudo-code for ETL migration
def migrate_telemetry_data():
    """
    1. Read data in batches from source table
    2. Parse and validate timestamps
    3. Convert to proper TIMESTAMP format
    4. Write to new partitioned table
    5. Validate data integrity
    """
    
    # Example timestamp conversion
    from datetime import datetime
    
    def convert_timestamp(varchar_ts):
        # Handle format: "2025-08-13T06:08:46.600648Z"
        return datetime.fromisoformat(varchar_ts.replace('Z', '+00:00'))
```

#### 3.3 Migration Phases
1. **Test Migration** (Dev environment)
   - Migrate subset of data (1 day)
   - Validate all queries work
   - Performance testing

2. **Parallel Run** (Production)
   - Create new tables alongside existing
   - Dual-write new data to both tables
   - Gradually migrate historical data

3. **Cutover**
   - Update applications to use new tables
   - Monitor for issues
   - Keep old tables for rollback

### Phase 4: Query Optimization (Day 5)

#### 4.1 Updated Query Templates
```sql
-- Before (with CAST)
SELECT COUNT(DISTINCT t.customer_id) as unique_viewers
FROM acme_telemetry.telemetry t 
WHERE CAST(t.event_timestamp AS timestamp) >= current_timestamp - INTERVAL '2' HOUR
  AND t.event_type = 'start';

-- After (native timestamp)
SELECT COUNT(DISTINCT t.customer_id) as unique_viewers
FROM acme_telemetry.telemetry_v2 t 
WHERE t.event_timestamp >= current_timestamp - INTERVAL '2' HOUR
  AND t.event_type = 'start';
```

#### 4.2 Performance Improvements
- **Expected Query Speed**: 30-50% faster for time-based queries
- **Reduced CPU Usage**: No runtime type conversion
- **Better Partition Pruning**: Date-based partitions
- **Improved Statistics**: Better query planning

### Phase 5: Implementation Checklist

#### Pre-Migration
- [ ] Backup existing table definitions
- [ ] Document all dependent queries
- [ ] Create test environment
- [ ] Prepare rollback plan
- [ ] Notify stakeholders

#### Migration
- [ ] Create new Glue tables with proper types
- [ ] Set up data migration jobs
- [ ] Implement dual-write for new data
- [ ] Migrate historical data in batches
- [ ] Validate data integrity

#### Post-Migration
- [ ] Update all query templates
- [ ] Update agent system prompt with new schema
- [ ] Performance testing and validation
- [ ] Update documentation
- [ ] Monitor for issues

#### Cleanup (After 30 days)
- [ ] Remove old tables
- [ ] Clean up compatibility views
- [ ] Archive old query templates
- [ ] Final performance report

## Risk Mitigation

### Potential Risks
1. **Data Loss**: Mitigated by parallel run and validation
2. **Query Failures**: Mitigated by compatibility views
3. **Performance Degradation**: Mitigated by testing
4. **Rollback Complexity**: Mitigated by keeping old tables

### Rollback Plan
1. Keep original tables for 30 days
2. Maintain compatibility views
3. Document rollback procedure
4. Test rollback in dev environment

## Expected Benefits

### Immediate Benefits
- ✅ Eliminate CAST operations in queries
- ✅ Reduce query errors
- ✅ Simpler, more readable SQL
- ✅ Better IDE/tool support

### Long-term Benefits
- ✅ 30-50% query performance improvement
- ✅ Reduced AWS Athena costs
- ✅ Better data governance
- ✅ Easier maintenance
- ✅ Foundation for advanced analytics

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Discovery & Analysis | 1 day | Access to Glue catalog |
| Schema Design | 1 day | Completed analysis |
| Migration Development | 2 days | Approved schema |
| Testing | 2 days | Migration scripts ready |
| Production Migration | 3 days | Testing complete |
| Monitoring & Optimization | Ongoing | Migration complete |

**Total Timeline**: 9 days for full migration

## Success Metrics

1. **Query Performance**
   - Baseline: Current p95 query time
   - Target: 40% reduction in p95 query time

2. **Error Rate**
   - Baseline: Current CAST error rate
   - Target: 0% type conversion errors

3. **Developer Experience**
   - Simpler queries (no CAST required)
   - Faster development cycle
   - Reduced debugging time

## Next Steps

1. **Immediate Action**: 
   - Get approval for schema changes
   - Set up test environment
   - Begin discovery phase

2. **Week 1**:
   - Complete analysis and design
   - Start migration development

3. **Week 2**:
   - Execute migration
   - Monitor and optimize

## Appendix

### A. Current Schema Issues in Agent Code

From `strands_claude.py`:
```python
# Current workaround in system prompt
"- Always use CAST(event_timestamp AS timestamp) for time filtering"
"- Use lowercase values: event_type = 'start', title_type = 'movie'"

# After migration, this can be simplified to:
"- Direct timestamp comparisons supported"
"- Consistent data types across all tables"
```

### B. Sample Migration Queries

```sql
-- Check for problematic timestamps
SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN try_cast(event_timestamp AS timestamp) IS NULL THEN 1 END) as invalid_timestamps
FROM acme_telemetry.telemetry;

-- Identify format variations
SELECT 
    REGEXP_EXTRACT(event_timestamp, '^[0-9]{4}-[0-9]{2}-[0-9]{2}') as date_part,
    COUNT(*) as count
FROM acme_telemetry.telemetry
GROUP BY 1
ORDER BY 2 DESC;
```

### C. AWS Glue API Commands

```bash
# Get current table definition
aws glue get-table \
    --database-name acme_telemetry \
    --name telemetry \
    --region eu-central-1

# Update table schema
aws glue update-table \
    --database-name acme_telemetry \
    --table-input file://new-table-schema.json \
    --region eu-central-1
```

### D. Monitoring Queries

```sql
-- Monitor migration progress
SELECT 
    DATE(event_timestamp) as event_date,
    COUNT(*) as record_count,
    'old_table' as source
FROM acme_telemetry.telemetry
GROUP BY 1
UNION ALL
SELECT 
    DATE(event_timestamp) as event_date,
    COUNT(*) as record_count,
    'new_table' as source
FROM acme_telemetry.telemetry_v2
GROUP BY 1
ORDER BY event_date, source;
```

## Contact & Resources

- **Project Owner**: ACME Corp Data Engineering Team
- **AWS Account**: 241533163649
- **Region**: eu-central-1
- **Glue Catalog**: [AWS Console Link]
- **Athena Workgroup**: primary
- **S3 Bucket**: acme-athena-results-241533163649

---

*Document Version: 1.0*
*Created: 2025-08-25*
*Status: DRAFT - Pending Approval*