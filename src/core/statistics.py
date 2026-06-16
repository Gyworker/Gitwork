"""
统计分析模块
提供任务统计和数据分析功能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict


class StatisticsService:
    """统计分析服务"""
    
    def __init__(self, task_model):
        self.task_model = task_model
        
    def get_task_summary(self) -> Dict[str, Any]:
        """获取任务统计摘要"""
        all_tasks = self.task_model.get_all_tasks()
        
        summary = {
            'total': len(all_tasks),
            'by_status': self._count_by_field(all_tasks, 'status'),
            'by_importance': self._count_by_field(all_tasks, 'importance'),
            'today_created': 0,
            'today_completed': 0
        }
        
        # 统计今日创建和完成的任务
        today = datetime.now().date()
        for task in all_tasks:
            create_time = task.get('task_time', '')
            if create_time:
                if isinstance(create_time, str):
                    try:
                        create_date = datetime.strptime(create_time[:10], '%Y-%m-%d').date()
                        if create_date == today:
                            summary['today_created'] += 1
                    except:
                        pass
                        
            if task.get('status') == '完成':
                # 检查是否今天完成
                # TODO: 需要记录完成时间字段
                summary['today_completed'] += 1
                
        return summary
        
    def get_status_distribution(self) -> List[Dict[str, Any]]:
        """获取任务状态分布"""
        all_tasks = self.task_model.get_all_tasks()
        counts = self._count_by_field(all_tasks, 'status')
        
        total = len(all_tasks)
        distribution = []
        
        status_labels = {
            '进行中': '进行中',
            '挂起': '挂起',
            '已答复': '已答复',
            '完成': '已完成'
        }
        
        for status, count in counts.items():
            percentage = (count / total * 100) if total > 0 else 0
            distribution.append({
                'status': status_labels.get(status, status),
                'count': count,
                'percentage': round(percentage, 1)
            })
            
        return distribution
        
    def get_importance_distribution(self) -> List[Dict[str, Any]]:
        """获取重要程度分布"""
        all_tasks = self.task_model.get_all_tasks()
        counts = self._count_by_field(all_tasks, 'importance')
        
        total = len(all_tasks)
        distribution = []
        
        importance_labels = {
            '高': '高优先级',
            '中': '中优先级',
            '低': '低优先级'
        }
        
        for importance, count in counts.items():
            percentage = (count / total * 100) if total > 0 else 0
            distribution.append({
                'importance': importance_labels.get(importance, importance),
                'count': count,
                'percentage': round(percentage, 1)
            })
            
        return distribution
        
    def get_responder_stats(self) -> List[Dict[str, Any]]:
        """获取责任人统计"""
        all_tasks = self.task_model.get_all_tasks()
        
        responder_counts = defaultdict(int)
        responder_in_progress = defaultdict(int)
        
        for task in all_tasks:
            responder = task.get('responder_name', '')
            if responder:
                responder_counts[responder] += 1
                if task.get('status') == '进行中':
                    responder_in_progress[responder] += 1
                    
        stats = []
        for responder, count in responder_counts.items():
            stats.append({
                'responder': responder,
                'total_tasks': count,
                'in_progress': responder_in_progress.get(responder, 0)
            })
            
        # 按任务总数排序
        stats.sort(key=lambda x: x['total_tasks'], reverse=True)
        
        return stats[:10]  # 返回前10
        
    def get_module_stats(self) -> List[Dict[str, Any]]:
        """获取关键模块统计"""
        all_tasks = self.task_model.get_all_tasks()
        
        module_counts = defaultdict(int)
        
        for task in all_tasks:
            key_module = task.get('key_module', '')
            if key_module:
                # 分割多个模块
                modules = [m.strip() for m in key_module.replace('/', ',').split(',')]
                for module in modules:
                    if module:
                        module_counts[module] += 1
                        
        stats = []
        for module, count in module_counts.items():
            stats.append({
                'module': module,
                'count': count
            })
            
        # 按数量排序
        stats.sort(key=lambda x: x['count'], reverse=True)
        
        return stats[:10]  # 返回前10
        
    def get_weekly_trend(self, weeks: int = 4) -> List[Dict[str, Any]]:
        """获取周趋势数据"""
        all_tasks = self.task_model.get_all_tasks()
        
        # 计算日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=weeks*7)
        
        # 按周统计
        weekly_data = defaultdict(lambda: {'created': 0, 'completed': 0})
        
        for task in all_tasks:
            create_time = task.get('task_time', '')
            if create_time:
                try:
                    if isinstance(create_time, str):
                        create_date = datetime.strptime(create_time[:10], '%Y-%m-%d').date()
                    else:
                        create_date = create_time.date()
                        
                    if start_date <= create_date <= end_date:
                        week_num = (create_date - start_date).days // 7 + 1
                        weekly_data[f'第{week_num}周']['created'] += 1
                except:
                    pass
                    
            # TODO: 统计完成数量需要完成时间字段
                    
        # 转换为列表
        trend = []
        for i in range(1, weeks + 1):
            week_key = f'第{i}周'
            trend.append({
                'week': week_key,
                'created': weekly_data[week_key]['created'],
                'completed': weekly_data[week_key]['completed']
            })
            
        return trend
        
    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """获取逾期任务"""
        all_tasks = self.task_model.get_all_tasks()
        overdue = []
        
        now = datetime.now()
        
        for task in all_tasks:
            if task.get('status') in ['完成', '已答复']:
                continue
                
            expected_time = task.get('expected_time', '')
            if expected_time:
                try:
                    if isinstance(expected_time, str):
                        deadline = datetime.strptime(expected_time[:19], '%Y-%m-%d %H:%M:%S')
                    else:
                        deadline = expected_time
                        
                    if deadline < now:
                        days_overdue = (now - deadline).days
                        overdue.append({
                            'task_id': task.get('task_id'),
                            'task_name': task.get('task_name'),
                            'responder': task.get('responder_name', ''),
                            'overdue_days': days_overdue,
                            'importance': task.get('importance', '')
                        })
                except:
                    pass
                    
        # 按逾期天数排序
        overdue.sort(key=lambda x: x['overdue_days'], reverse=True)
        
        return overdue
        
    def generate_summary_report(self) -> str:
        """生成统计摘要报告"""
        summary = self.get_task_summary()
        status_dist = self.get_status_distribution()
        importance_dist = self.get_importance_distribution()
        overdue = self.get_overdue_tasks()
        
        report = []
        report.append("=" * 50)
        report.append("任务统计摘要报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 50)
        report.append("")
        
        report.append("【总体统计】")
        report.append(f"任务总数: {summary['total']}")
        report.append(f"今日新增: {summary['today_created']}")
        report.append(f"今日完成: {summary['today_completed']}")
        report.append("")
        
        report.append("【状态分布】")
        for item in status_dist:
            report.append(f"  {item['status']}: {item['count']} ({item['percentage']}%)")
        report.append("")
        
        report.append("【重要程度分布】")
        for item in importance_dist:
            report.append(f"  {item['importance']}: {item['count']} ({item['percentage']}%)")
        report.append("")
        
        if overdue:
            report.append(f"【逾期任务】({len(overdue)}个)")
            for task in overdue[:5]:
                report.append(f"  - {task['task_name']} (逾期{task['overdue_days']}天)")
        else:
            report.append("【逾期任务】无")
            
        report.append("")
        report.append("=" * 50)
        
        return "\n".join(report)
        
    def _count_by_field(self, tasks: List[Dict[str, Any]], field: str) -> Dict[str, int]:
        """按字段统计数量"""
        counts = defaultdict(int)
        for task in tasks:
            value = task.get(field, '未知')
            if value:
                counts[value] += 1
        return dict(counts)
