# Use NVIDIA CUDA runtime as the base image
FROM nvidia/cuda:11.1.1-cudnn8-runtime-ubuntu20.04

# Set timezone
ENV TZ=Europe/Istanbul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install Python 3.8 and necessary system dependencies
RUN : \
    && apt-get update \
    && apt-get install -y git curl \
    && apt-get install -y --no-install-recommends software-properties-common \
    && add-apt-repository -y ppa:deadsnakes \
    && apt-get install -y --no-install-recommends python3.8-venv python3.8-dev \
    && apt-get install -y libffi-dev libxml2-dev libjpeg-turbo8-dev zlib1g-dev \
    && apt-get install -y libgl1 libglib2.0-0 mesa-utils \
    && apt-get clean \
    && :

# Create and activate Python virtual environment
RUN python3.8 -m venv /venv
ENV PATH=/venv/bin:$PATH

# Install pip and necessary Python packages
RUN /venv/bin/python3.8 -m pip install --no-cache-dir --upgrade pip setuptools wheel

# Install OpenSlide and its Python bindings
RUN : \
    && apt-get update \
    && apt-get install -y openslide-tools libopenslide0 \
    && apt-get clean \
    && : \
    && /venv/bin/python3.8 -m pip install openslide-python

# Install additional dependencies
RUN /venv/bin/python3.8 -m pip install tifffile numpy scikit-image

# Add user for container security
RUN groupadd -r user && useradd -m --no-log-init -r -g user user
RUN chown -R user:user /venv/

# Set working directory
USER user
WORKDIR /opt/app

# Copy your program files
COPY --chown=user:user main.py /opt/app/
COPY --chown=user:user utils /opt/app/utils
# COPY --chown=user:user input /opt/app/input
# COPY --chown=user:user output /opt/app/output
COPY --chown=user:user requirements.txt /opt/app/
COPY --chown=user:user best.pt /opt/app/
# COPY --chown=user:user Patches /opt/app/Patches
COPY --chown=user:user generate_dummy_eval.py /opt/app/

# Install Python dependencies from requirements.txt
RUN /venv/bin/python3.8 -m pip install --no-cache-dir -r /opt/app/requirements.txt

# Install PyTorch
RUN /venv/bin/python3.8 -m pip install torch==1.13.1+cu116 torchvision==0.14.1+cu116 torchaudio==0.13.1 --extra-index-url https://download.pytorch.org/whl/cu116
# RUN /venv/bin/python3.8 -m pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu111/torch1.10/index.html

# Install YOLOv8
RUN /venv/bin/python3.8 -m pip install ultralytics

# Install Whole Slide Data library
# RUN /venv/bin/python3.8 -m pip install 'git+https://github.com/DIAGNijmegen/pathology-whole-slide-data@main'

# Ensure Python output is not buffered
ENV PYTHONUNBUFFERED=1
ENV YOLO_CONFIG_DIR=/opt/app/.ultralytics_config
RUN mkdir -p /opt/app/.ultralytics_config && chown -R user:user /opt/app/.ultralytics_config

# Set entrypoint to execute main.py
RUN /venv/bin/python3.8 generate_dummy_eval.py
ENTRYPOINT ["/venv/bin/python3.8", "main.py"]
