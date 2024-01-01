FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy the application code to the container
COPY . /app
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
CMD [ "python", "bot.py" ]
