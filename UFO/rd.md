```python
data = pickle.load(open('cache.pkl','rb')) if os.path.exists('cache.pkl') else pickle.dump((data:=load_data()), open('cache.pkl','wb')) or data
```