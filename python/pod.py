import json
import requests
from collections import defaultdict

def get_pod_stats(json_data):
    """
    统计所有Pod的资源request总和
    :param json_data: kubelet pod接口返回的JSON数据
    :return: 资源统计结果
    """
    total_requests = {
        'cpu': 0.0,
        'memory': 0.0
    }
    
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data
    
    pods = data.get('items', [])
    
    for pod in pods:
        pod_requests = calculate_pod_requests(pod)
        total_requests['cpu'] += pod_requests['cpu']
        total_requests['memory'] += pod_requests['memory']
    
    return total_requests

def calculate_pod_requests(pod):
    """
    计算单个Pod的有效资源request
    规则：always initContainer + 所有container 与 其他initContainer 取max
    """
    spec = pod.get('spec', {})
    
    # 获取所有常规container的request总和
    containers = spec.get('containers', [])
    container_requests = {'cpu': 0.0, 'memory': 0.0}
    for container in containers:
        requests = container.get('resources', {}).get('requests', {})
        container_requests['cpu'] += parse_cpu(requests.get('cpu', '0'))
        container_requests['memory'] += parse_memory(requests.get('memory', '0'))
    
    # 获取initContainer
    init_containers = spec.get('initContainers', [])
    
    # 分离always类型和其他initContainer
    always_init_requests = {'cpu': 0.0, 'memory': 0.0}
    other_init_max = {'cpu': 0.0, 'memory': 0.0}
    
    for init_container in init_containers:
        requests = init_container.get('resources', {}).get('requests', {})
        cpu = parse_cpu(requests.get('cpu', '0'))
        memory = parse_memory(requests.get('memory', '0'))
        
        # 检查restartPolicy，默认为非always
        restart_policy = init_container.get('restartPolicy', '')
        
        if restart_policy == 'Always':
            always_init_requests['cpu'] += cpu
            always_init_requests['memory'] += memory
        else:
            other_init_max['cpu'] = max(other_init_max['cpu'], cpu+always_init_requests['cpu'])
            other_init_max['memory'] = max(other_init_max['memory'], memory+always_init_requests['memory'])
    
    # 计算最终request: max(always + containers, other_init)
    final_requests = {
        'cpu': max(
            always_init_requests['cpu'] + container_requests['cpu'],
            other_init_max['cpu']
        ),
        'memory': max(
            always_init_requests['memory'] + container_requests['memory'],
            other_init_max['memory']
        )
    }
    
    print(f"{pod.get('metadata', {}).get('name')}: {final_requests}")
    return final_requests

def parse_cpu(cpu_str):
    """解析CPU字符串，转换为cores"""
    if not cpu_str or cpu_str == '0':
        return 0.0
    if cpu_str.endswith('m'):
        return float(cpu_str[:-1]) / 1000
    return float(cpu_str)

def parse_memory(memory_str):
    """解析内存字符串，转换为字节"""
    if not memory_str or memory_str == '0':
        return 0.0
    
    units = {
        'Ki': 1024,
        'Mi': 1024 ** 2,
        'Gi': 1024 ** 3,
        'Ti': 1024 ** 4,
        'K': 1000,
        'M': 1000 ** 2,
        'G': 1000 ** 3,
        'T': 1000 ** 4
    }
    
    for unit, multiplier in units.items():
        if memory_str.endswith(unit):
            return float(memory_str[:-len(unit)]) * multiplier
    
    return float(memory_str)

def format_output(total_requests):
    """格式化输出结果"""
    print("=" * 50)
    print("Pod Resource Request 统计结果")
    print("=" * 50)
    print(f"总CPU Request:    {total_requests['cpu']:.2f} cores")
    print(f"总Memory Request: {total_requests['memory'] / (1024**3):.2f} Gi")
    print(f"                  {total_requests['memory'] / (1024**2):.2f} Mi")
    print("=" * 50)

if __name__ == "__main__":
    with open('pods.json', 'r') as f:
        json_data = json.load(f)
    
    total_requests = get_pod_stats(json_data)
    format_output(total_requests)