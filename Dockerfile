

FROM public.ecr.aws/emr-serverless/spark/emr-7.1.0@sha256:4a8e05f528fa08c00a20a22ced7ccb279d1e166c39a18b46a3abecefa7df7daa

USER root

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=hadoop:hadoop src/ /app/src/

ENV PYTHONPATH="/app:${PYTHONPATH}"

# EMR Serverless requires the final image to run as the hadoop user
USER hadoop:hadoop