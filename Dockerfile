

FROM public.ecr.aws/emr-serverless/spark/emr-7.1.0:latest

USER root

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=hadoop:hadoop src/ /app/src/

ENV PYTHONPATH="/app:${PYTHONPATH}"

# EMR Serverless requires the final image to run as the hadoop user
USER hadoop:hadoop