import React, { useState } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  onCategoryChange: (category: string) => void;
  selectedCategory: string;
}

const categories = [
  { value: '', label: 'All Categories' },
  { value: 'documentation', label: 'Documentation' },
  { value: 'data', label: 'Data & Analytics' },
  { value: 'vision', label: 'Vision & Image' },
  { value: 'generation', label: 'Generation' },
  { value: 'other', label: 'Other' },
];

export const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  onCategoryChange,
  selectedCategory,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchQuery);
  };

  return (
    <div style={styles.container}>
      <form onSubmit={handleSearch} style={styles.searchForm}>
        <input
          type="text"
          placeholder="Search MCP servers..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={styles.searchInput}
        />
        <button type="submit" style={styles.searchBtn}>
          Search
        </button>
      </form>

      <select
        value={selectedCategory}
        onChange={(e) => onCategoryChange(e.target.value)}
        style={styles.categorySelect}
      >
        {categories.map((cat) => (
          <option key={cat.value} value={cat.value}>
            {cat.label}
          </option>
        ))}
      </select>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    gap: '16px',
    marginBottom: '24px',
    flexWrap: 'wrap',
  },
  searchForm: {
    display: 'flex',
    flex: 1,
    minWidth: '300px',
  },
  searchInput: {
    flex: 1,
    padding: '10px 16px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '4px 0 0 4px',
    outline: 'none',
  },
  searchBtn: {
    padding: '10px 20px',
    fontSize: '14px',
    backgroundColor: '#ff9900',
    color: 'white',
    border: 'none',
    borderRadius: '0 4px 4px 0',
    cursor: 'pointer',
    fontWeight: '500',
  },
  categorySelect: {
    padding: '10px 16px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    outline: 'none',
    backgroundColor: 'white',
    minWidth: '180px',
  },
};
