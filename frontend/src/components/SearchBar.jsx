function SearchBar({ value, onChange, placeholder = "Search" }) {
  return <label className="search-bar"><span>⌕</span><input value={value} onChange={onChange} placeholder={placeholder} aria-label={placeholder} /></label>;
}

export default SearchBar;
