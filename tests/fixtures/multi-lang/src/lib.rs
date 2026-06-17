//! Native Rust library exposed to Python via PyO3.

pub fn process(data: &[f64]) -> Vec<f64> {
    data.iter().map(|x| x * 2.0).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_process() {
        let result = process(&[1.0, 2.0, 3.0]);
        assert_eq!(result, vec![2.0, 4.0, 6.0]);
    }
}
