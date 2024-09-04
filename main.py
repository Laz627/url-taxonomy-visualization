import streamlit as st
import pandas as pd
from streamlit_markmap import markmap
import io
import base64
import json

# Set page config at the very beginning
st.set_page_config(layout="wide", page_title="URL Taxonomy Visualizer")

def download_template():
    template_df = pd.DataFrame({
        'Full URL': ['https://example.com/page1', 'https://example.com/page2'],
        'L0': ['Category1', 'Category2'],
        'L1': ['Subcategory1', 'Subcategory2'],
        'L2': ['SubSubcategory1', 'SubSubcategory2'],
    })
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        template_df.to_excel(writer, sheet_name='Template', index=False)
    
    b64 = base64.b64encode(buffer.getvalue()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="template.xlsx">Download Excel Template</a>'
    return href

@st.cache_data
def load_data(uploaded_file):
    try:
        data = pd.read_excel(uploaded_file)
        data = data.drop_duplicates(subset=['Full URL'])
        st.success(f"Data loaded successfully. Shape after removing duplicates: {data.shape}")
        return data
    except Exception as e:
        st.error(f"An error occurred while loading the data: {str(e)}")
        st.stop()

def add_to_tree(tree, path, url):
    current = tree
    for component in path:
        if component not in current['children']:
            current['children'][component] = {'name': component, 'children': {}, 'urls': [], 'count': 0}
        current = current['children'][component]
        current['count'] += 1
    current['urls'].append(url)

def create_markmap_data(tree):
    result = []
    for key, value in sorted(tree['children'].items()):
        node = {
            'name': f"{key} ({value['count']})",
            'children': create_markmap_data(value)
        }
        if value['urls']:
            node['children'].append({
                'name': 'URLs',
                'children': [{'name': url} for url in sorted(value['urls'])]
            })
        result.append(node)
    return result

def process_data(data):
    category_tree = {'name': 'URL Hierarchy', 'children': {}}
    problematic_urls = []
    for _, row in data.iterrows():
        url = row['Full URL']
        category_path = [str(row[f'L{i}']) for i in range(8) if pd.notna(row[f'L{i}'])]
        if not category_path:
            problematic_urls.append(url)
            continue
        add_to_tree(category_tree, category_path, url)
    
    if problematic_urls:
        st.warning("The following URLs couldn't be properly categorized:")
        st.write(problematic_urls)
    
    return category_tree

# Streamlit UI
st.title("Hierarchical Visualization of URLs with Counts and Colors")

# Download template
st.markdown("### Download Template")
st.markdown(download_template(), unsafe_allow_html=True)

# File uploader
st.markdown("### Upload Your Excel File")
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    # Load data
    data = load_data(uploaded_file)

    # Process data into a tree structure based on the category columns
    category_tree = process_data(data)

    # Create markmap data
    markmap_data = create_markmap_data(category_tree)

    # Convert to JSON
    markmap_json = json.dumps(markmap_data)

    # Markmap configuration
    markmap_options = {
        'colorFreezeLevel': 2,
        'initialExpandLevel': 3,
    }

    # CSS to control the size of the markmap and hide URLs
    st.markdown("""
        <style>
        .stMarkmap > div {
            height: 600px;
            width: 100%;
        }
        .markmap-node-text:not(:hover) .mm-url {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)

    # Render the markmap
    markmap(markmap_json, options=markmap_options)

    # Provide user interaction for opening URLs
    st.markdown("""
    ### Click on the URLs below to navigate
    """)
    selected_url = st.selectbox('Select URL to open', sorted(data['Full URL'].unique()))
    if st.button('Open URL'):
        st.write(f"Opening URL: {selected_url}")
        st.markdown(f'<a href="{selected_url}" target="_blank">Click here to open the URL</a>', unsafe_allow_html=True)
else:
    st.info("Please upload an Excel file to visualize the URL hierarchy.")
