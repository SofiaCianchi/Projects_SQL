#!/usr/bin/env python
# coding: utf-8

# # Guided Project on Chinook database
# 
# This is my execution of the DataQuest Guided Project. This project is guided insofar as the DataQuest platform provides a set of prompts to be answered using SQL to analyze the Chinook database.
# 
# The Chinook SQLite database file represents a digital media store with information on track sales, customer ids, etc. This is a sample database which uses partially real iTunes data, but was created for SQL practice.

# ### Connect Chinook database

# In[1]:


get_ipython().run_cell_magic('capture', '', '%load_ext sql\n%sql sqlite:///chinook.db')


# ### Explore

# In[2]:


get_ipython().run_cell_magic('sql', '', 'SELECT\n    name,\n    type\nFROM sqlite_master\nWHERE type IN ("table","view");')


# ### Which genres sell the most tracks in the U.S.?

# In[3]:


get_ipython().run_cell_magic('sql', '', '\nWITH tracks_sold_usa AS\n                       (\n                        SELECT il.* \n                        FROM invoice_line il\n                        INNER JOIN invoice i ON il.invoice_id = i.invoice_id\n                        INNER JOIN customer c ON i.customer_id = c.customer_id\n                        WHERE c.country = "USA"\n                       )\n    \nSELECT g.name genre, \n       COUNT(tsu.invoice_line_id) sold_by_genre,\n       ROUND(CAST(COUNT(tsu.invoice_line_id) AS FLOAT) / \n        (\n        SELECT COUNT(*) from tracks_sold_usa\n        ), 3) percentage\nFROM tracks_sold_usa tsu\nINNER JOIN track t ON t.track_id = tsu.track_id\nINNER JOIN genre g ON g.genre_id = t.genre_id\nGROUP BY 1 \nORDER BY 2 DESC;            ')


# ### For each country, calculate:
# * total number of customers
# * total value of sales
# * average value of sales per customer
# * average order value

# In[4]:


get_ipython().run_cell_magic('sql', '', '\nWITH joined_table AS \n                   (\n                    SELECT \n                      CASE WHEN (\n                            SELECT COUNT(*)\n                            FROM customer\n                            WHERE country = c.country\n                            ) = 1 THEN "Other"\n                           ELSE c.country\n                           END \n                           AS country, \n                       c.customer_id, \n                       i.invoice_id, \n                       i.total\n                    FROM customer c\n                    INNER JOIN invoice i ON i.customer_id = c.customer_id\n                   )\n\nSELECT country, \n       COUNT(DISTINCT customer_id) n_customers, \n       ROUND(SUM(total),3) total_sales,\n       ROUND(SUM(total) / COUNT(DISTINCT customer_id), 3) avg_sales_per_customer,\n       ROUND(SUM(total) / (\n                      SELECT COUNT(j.invoice_id)\n                      FROM joined_table\n                      GROUP BY country\n                      ),3) avg_order_value\nFROM joined_table j\nGROUP BY 1 ORDER BY country = "Other" ASC, 3 DESC;')


# ### What percentage of purchases are albums v. individual tracks?
# The digital media store allows to purchase either a full album or on or more individual tracks, but not a mix of both. 
# 
# _There is an edge case which prevents a completely accurate analysis: customers can manually select all individual tracks from one album and then add more individual tracks. If this occurs, the purchase will be a mix of full albums and individual tracks, but in the analysis below it will be included in the percentage of individual tracks._

# In[14]:


get_ipython().run_cell_magic('sql', '', '\nWITH a_track_per_invoice AS \n                (\n                SELECT invoice_id, MAX(track_id) track_id\n                FROM invoice_line il\n                GROUP BY invoice_id\n                ),\n    \nalbum_vs_individual AS\n    (\n    SELECT  a_track_per_invoice.*,\n        CASE \n           WHEN (\n                 SELECT il2.track_id FROM invoice_line il2\n                 WHERE il2.invoice_id = a_track_per_invoice.invoice_id\n    \n                 EXCEPT\n        \n                 SELECT t.track_id FROM track t\n                 WHERE t.album_id = (SELECT tr.album_id FROM track tr\n                                WHERE tr.track_id = a_track_per_invoice.track_id)\n                )\n        IS NULL\n        \n        AND (\n            SELECT t.track_id FROM track t\n                 WHERE t.album_id = (SELECT tr.album_id FROM track tr\n                                WHERE tr.track_id = a_track_per_invoice.track_id)\n            EXCEPT\n            \n            SELECT il2.track_id FROM invoice_line il2\n                 WHERE il2.invoice_id = a_track_per_invoice.invoice_id\n            )\n        \n        THEN "yes"\n        ELSE "no"\n        END AS album_purchase\nFROM a_track_per_invoice\n    )\n\n        \nSELECT album_purchase, \n       COUNT(invoice_id) n_invoices, \n       ROUND(CAST(COUNT(invoice_id) AS FLOAT) / (SELECT COUNT * FROM invoice), 3) percent_invoices\nFROM album_vs_individual\nGROUP BY album_purchase')


# In[29]:


get_ipython().run_cell_magic('sql', '', '\nWITH a_track_per_invoice AS \n                (\n                SELECT invoice_id, MAX(track_id) track_id\n                FROM invoice_line il\n                GROUP BY invoice_id\n                ),\n    \nalbum_vs_individual AS\n    (\n    SELECT  a_track_per_invoice.*,\n        CASE \n           WHEN (\n                 SELECT il2.track_id FROM invoice_line il2\n                 WHERE il2.invoice_id = a_track_per_invoice.invoice_id\n    \n                 EXCEPT\n        \n                 SELECT t.track_id FROM track t\n                 WHERE t.album_id = (SELECT tr.album_id FROM track tr\n                                WHERE tr.track_id = a_track_per_invoice.track_id)\n                )\n        IS NULL\n        \n        AND (\n            SELECT t.track_id FROM track t\n                 WHERE t.album_id = (SELECT tr.album_id FROM track tr\n                                WHERE tr.track_id = a_track_per_invoice.track_id)\n            EXCEPT\n            \n            SELECT il2.track_id FROM invoice_line il2\n                 WHERE il2.invoice_id = a_track_per_invoice.invoice_id\n            )\n        \n        IS NULL\n        \n        THEN "Individual_tracks"\n        ELSE "Album"\n        END AS album_purchase\nFROM a_track_per_invoice\n    )\n\nSELECT album_purchase, \n       COUNT(invoice_id) n_of_invoices,\n       ROUND(CAST(COUNT(invoice_id) AS FLOAT) / (SELECT COUNT(*) FROM invoice), 3) percentage\nFROM album_vs_individual\nGROUP BY album_purchase')


# ### Which artists are most used in most playlists?

# In[7]:


get_ipython().run_cell_magic('sql', '', '\nWITH new_table AS \n                (\n                 SELECT * \n                 FROM artist a\n                 LEFT JOIN album al ON al.artist_id = a.artist_id\n                 LEFT JOIN track t ON t.album_id = al.album_id\n                 LEFT JOIN playlist_track p ON p.track_id = t.track_id\n                )\n    \nSELECT name, COUNT(DISTINCT playlist_id) n_playlists\nFROM new_table\nGROUP BY 1 ORDER BY 2 DESC\nLIMIT 10;')


# ### How does the range of tracks in the store compare to their popularity?
# I define "range" as genre and "popularity" as tracks sold. I use and modify the code from line 4.

# In[8]:


get_ipython().run_cell_magic('sql', '', '\nWITH tracks_sold AS\n                    (\n                    SELECT il.* \n                    FROM invoice_line il\n                    INNER JOIN invoice i ON il.invoice_id = i.invoice_id\n                    INNER JOIN customer c ON i.customer_id = c.customer_id\n                    ),\n    \ntracks_sold_by_genre AS \n                      (\n                      SELECT g.name genre, \n                      COUNT(ts.invoice_line_id) sold_by_genre,\n                      ROUND(CAST(COUNT(ts.invoice_line_id) AS FLOAT) / \n                      (\n                      SELECT COUNT(*) from tracks_sold\n                      ), 3) percentage_sold\n                      FROM tracks_sold ts\n                      INNER JOIN track t ON t.track_id = ts.track_id\n                      INNER JOIN genre g ON g.genre_id = t.genre_id\n                      GROUP BY 1 \n                      ORDER BY 2 DESC\n                      )\n\nSELECT g.name genre, \n       ROUND(CAST(COUNT(track_id) AS FLOAT) / (\n        SELECT COUNT(*) FROM track\n       ), 3) percentage_in_store,\n       percentage_sold \nFROM track t\nINNER JOIN genre g ON g.genre_id = t.genre_id\nINNER JOIN tracks_sold_by_genre tt ON tt.genre = g.name\nGROUP BY 1 ORDER BY 2 DESC;')

