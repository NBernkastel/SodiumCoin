import uvicorn

if __name__ == '__main__':
    uvicorn.run('api:app', host='192.168.0.102', port=8000, reload=True)
