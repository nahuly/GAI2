import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
from io import StringIO

# Streamlit app setup
st.title('Character Relationship Diagram Generator')

# File upload
uploaded_file = st.file_uploader("Upload a text file", type="txt")

st.write(uploaded_file)

# if uploaded_file is not None:
#     # Read the uploaded file
#     stringio = StringIO(uploaded_file.read().decode("utf-8"))
#     story_text = stringio.read()

#     # Create a relationship graph (example relationships)
#     G = nx.Graph()

#     # Example characters and relationships
#     G.add_edge("Henry Jekyll", "Edward Hyde", relationship="같은 인물")
#     G.add_edge("Henry Jekyll", "John Utterson", relationship="친구")
#     G.add_edge("Henry Jekyll", "Dr. Hastie Lanyon", relationship="동료")
#     G.add_edge("Henry Jekyll", "Emma Carew", relationship="약혼자")
#     G.add_edge("Emma Carew", "Danvers Carew", relationship="부녀")
#     G.add_edge("Edward Hyde", "Lucy", relationship="폭력적 관계")

#     # Plot the graph
#     pos = nx.spring_layout(G)
#     plt.figure(figsize=(8, 6))

#     nx.draw(G, pos, with_labels=True, node_color='lightblue',
#             font_weight='bold', node_size=3000)

#     # Add relationship labels to the edges
#     edge_labels = nx.get_edge_attributes(G, 'relationship')
#     nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

#     # Display the graph in Streamlit
#     st.pyplot(plt.gcf())  # Use plt.gcf() to get the current figure

#     # Close the plot after displaying
#     plt.clf()
